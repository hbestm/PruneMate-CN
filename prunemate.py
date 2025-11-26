import os
import json
import logging
import tempfile
import datetime
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash
from filelock import FileLock, Timeout
from gunicorn.app.base import BaseApplication
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

# optional docker import (best-effort)
try:
    import docker
except Exception:
    docker = None

# Application
app = Flask(__name__)
app.secret_key = os.environ.get("PRUNEMATE_SECRET", "prunemate-secret-key")

# Paths and defaults
CONFIG_PATH = Path(os.environ.get("PRUNEMATE_CONFIG", "/config/config.json"))
# File lock to serialize prune jobs across processes
LOCK_FILE = Path(os.environ.get("PRUNEMATE_LOCK", "/config/prunemate.lock"))
# File to persist the last run key so multiple workers don't double-trigger
LAST_RUN_FILE = Path(os.environ.get("PRUNEMATE_LAST_RUN", "/config/last_run_key"))
LAST_RUN_LOCK = Path(str(LAST_RUN_FILE) + ".lock")

DEFAULT_CONFIG = {
    "frequency": "daily",
    "time": "03:00",
    "day_of_week": "mon",
    "day_of_month": 1,
    "prune_containers": False,
    "prune_images": True,
    "prune_networks": False,
    "prune_volumes": False,
    "notifications": {
        "provider": "gotify",
        "gotify": {"enabled": False, "url": "", "token": ""},
        "ntfy": {"enabled": False, "url": "", "topic": ""},
        "only_on_changes": True,
    },
}

config = DEFAULT_CONFIG.copy()
# Lock to ensure thread-safe config read/write across workers
import threading
config_lock = threading.RLock()
# In-memory cache (best-effort) for last run; authoritative value is on disk
last_run_key = {"value": None}


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)
    try:
        Path("/var/log").mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler("/var/log/prunemate.log", maxBytes=5_000_000, backupCount=3)
        # Note: %(asctime)s uses system local time, not app_timezone
        # Custom log() function handles timezone-aware timestamps
        fh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(fh)
    except Exception:
        logger.exception("Failed to configure file logging; continuing with console only.")


configure_logging()


# Timezone
tz_name = os.environ.get("PRUNEMATE_TZ", "UTC")
try:
    app_timezone = ZoneInfo(tz_name)
except Exception:
    logging.warning("Invalid timezone '%s', falling back to UTC", tz_name)
    app_timezone = ZoneInfo("UTC")

logging.info("Using timezone: %s", app_timezone)

# Time format (12h or 24h)
use_24h_format = os.environ.get("PRUNEMATE_TIME_24H", "true").lower() in ("true", "1", "yes")
logging.info("Using time format: %s", "24-hour" if use_24h_format else "12-hour")

# Suppress verbose APScheduler job execution logs
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

# Scheduler
# Background scheduler for minute heartbeat. Jobs are added in __main__.
scheduler = BackgroundScheduler(
    timezone=app_timezone,
    job_defaults={
        "coalesce": False,
        "misfire_grace_time": 300,
    },
)
scheduler.start()


def log(message: str):
    now = datetime.datetime.now(app_timezone)
    timestamp = now.isoformat(timespec="seconds")
    logging.info("[%s] %s", timestamp, message)


def _redact_for_log(obj):
    """Return a deep-copied structure with secrets redacted for safe logging."""
    if isinstance(obj, dict):
        redacted = {}
        for k, v in obj.items():
            if k.lower() in {"token", "api_key", "apikey", "password", "secret"}:
                redacted[k] = "***"
            else:
                redacted[k] = _redact_for_log(v)
        return redacted
    if isinstance(obj, list):
        return [_redact_for_log(x) for x in obj]
    return obj


# ---- Cross-process last-run tracking (prevents duplicate scheduled triggers) ----
def _read_last_run_key() -> str | None:
    try:
        # Use a short lock to avoid concurrent reads/writes across workers
        with FileLock(str(LAST_RUN_LOCK)):
            if LAST_RUN_FILE.exists():
                return LAST_RUN_FILE.read_text(encoding="utf-8").strip() or None
    except Exception:
        # Best-effort: on any error, fall back to in-memory state
        pass
    return None


def _write_last_run_key(key: str) -> None:
    try:
        with FileLock(str(LAST_RUN_LOCK)):
            parent = LAST_RUN_FILE.parent
            parent.mkdir(parents=True, exist_ok=True)
            tmp = LAST_RUN_FILE.with_suffix(LAST_RUN_FILE.suffix + ".tmp")
            tmp.write_text(key, encoding="utf-8")
            try:
                tmp.chmod(0o600)
            except Exception:
                pass
            tmp.replace(LAST_RUN_FILE)
    except Exception:
        # Non-fatal: fall back to in-memory only
        pass


def _clear_last_run_key() -> None:
    last_run_key["value"] = None
    try:
        with FileLock(str(LAST_RUN_LOCK)):
            if LAST_RUN_FILE.exists():
                LAST_RUN_FILE.unlink()
    except Exception:
        pass


def human_bytes(num: int) -> str:
    n = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def format_time(time_str: str) -> str:
    """Format time string according to user preference (12h or 24h)."""
    if use_24h_format:
        return time_str
    # Convert 24h to 12h format
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = parts[1] if len(parts) > 1 else "00"
        
        if hour == 0:
            return f"12:{minute} AM"
        elif hour < 12:
            return f"{hour}:{minute} AM"
        elif hour == 12:
            return f"12:{minute} PM"
        else:
            return f"{hour - 12}:{minute} PM"
    except Exception:
        return time_str


def describe_schedule() -> str:
    freq = config.get("frequency", "daily")
    time_str = config.get("time", "03:00")
    formatted_time = format_time(time_str)
    if freq == "daily":
        return f"daily at {formatted_time} ({tz_name})"
    if freq == "weekly":
        day_key = config.get("day_of_week", "mon")
        day_names = {
            "mon": "Monday", "tue": "Tuesday", "wed": "Wednesday",
            "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday",
        }
        return f"weekly at {day_names.get(day_key, day_key)} {formatted_time} ({tz_name})"
    if freq == "monthly":
        day_of_month = config.get("day_of_month", 1)
        return f"monthly on day {day_of_month} at {formatted_time} ({tz_name})"
    return f"{freq} at {formatted_time} ({tz_name})"


def effective_config():
    freq = config.get("frequency", "daily")
    base = {
        "frequency": freq,
        "time": config.get("time"),
        "prune_containers": config.get("prune_containers"),
        "prune_images": config.get("prune_images"),
        "prune_networks": config.get("prune_networks"),
        "prune_volumes": config.get("prune_volumes"),
        "notifications": config.get("notifications"),
    }
    if freq == "weekly":
        base["day_of_week"] = config.get("day_of_week")
    elif freq == "monthly":
        base["day_of_month"] = config.get("day_of_month")
    return base


def load_config(silent=False):
    """Load configuration from disk. Set silent=True to suppress logging."""
    global config
    with config_lock:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)

            # Migrate legacy gotify keys into new notifications structure (best-effort)
            if any(k in data for k in ("gotify_enabled", "gotify_url", "gotify_token", "gotify_only_on_changes")):
                got = {
                    "enabled": bool(data.get("gotify_enabled")),
                    "url": (data.get("gotify_url") or "").strip(),
                    "token": (data.get("gotify_token") or "").strip(),
                }
                merged.setdefault("notifications", {}).update({
                    "provider": "gotify",
                    "gotify": got,
                    "only_on_changes": bool(data.get("gotify_only_on_changes", merged["notifications"]["only_on_changes"])),
                })
            # Ensure notifications key exists
            if "notifications" not in merged:
                merged["notifications"] = DEFAULT_CONFIG["notifications"].copy()

            config = merged
            if not silent:
                log(f"Loaded config from {CONFIG_PATH}: {_redact_for_log(effective_config())}")
        except FileNotFoundError:
            if not silent:
                log(f"No config file found at {CONFIG_PATH}, using defaults.")
            config = DEFAULT_CONFIG.copy()
        except Exception as e:
            if not silent:
                log(f"Error loading config from {CONFIG_PATH}: {e}. Using defaults.")
            config = DEFAULT_CONFIG.copy()


def save_config():
    """Atomic save with fsync and restricted permissions (best-effort)."""
    with config_lock:
        try:
            path = Path(CONFIG_PATH)
            parent = path.parent or Path(".")
            parent.mkdir(parents=True, exist_ok=True)

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile("w", delete=False, dir=str(parent), encoding="utf-8") as tmp:
                    json.dump(config, tmp, indent=2)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    tmp_path = Path(tmp.name)
                # try to restrict permissions (best-effort)
                try:
                    tmp_path.chmod(0o600)
                except Exception:
                    pass
                # atomic replace
                tmp_path.replace(path)
                log(f"Config saved to {path}: {_redact_for_log(effective_config())}")
            finally:
                # cleanup leftover temp if any
                if tmp_path and tmp_path.exists() and tmp_path != path:
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
        except Exception as e:
            log(f"Failed to save config to {CONFIG_PATH}: {e}")


def _send_gotify(cfg: dict, title: str, message: str, priority: int = 5) -> bool:
    if not cfg.get("enabled"):
        log("Gotify disabled; skipping notification.")
        return False
    url = (cfg.get("url") or "").strip()
    token = (cfg.get("token") or "").strip()
    if not url or not token:
        log("Gotify enabled but URL/token missing; skipping.")
        return False
    endpoint = url.rstrip("/") + "/message?token=" + token
    payload = json.dumps({"title": title, "message": message, "priority": priority}).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            log(f"Gotify notification sent, status={getattr(resp, 'status', '?')}")
            return True
    except Exception as e:
        log(f"Failed to send Gotify notification: {e}")
        return False


def _send_ntfy(cfg: dict, title: str, message: str, priority: int = 5) -> bool:
    if not cfg.get("enabled"):
        log("ntfy disabled; skipping notification.")
        return False
    url = (cfg.get("url") or "").strip()
    topic = (cfg.get("topic") or "").strip()
    if not url or not topic:
        log("ntfy enabled but URL/topic missing; skipping.")
        return False
    endpoint = url.rstrip("/") + "/" + topic.lstrip("/")
    headers = {"Title": title, "Priority": str(priority), "Content-Type": "text/plain"}
    payload = message.encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            log(f"ntfy notification sent, status={getattr(resp, 'status', '?')}")
            return True
    except Exception as e:
        log(f"Failed to send ntfy notification: {e}")
        return False


def send_notification(title: str, message: str, priority: int = 5) -> bool:
    notcfg = config.get("notifications", DEFAULT_CONFIG["notifications"])
    provider = (notcfg.get("provider") or "gotify").lower()
    if provider == "gotify":
        return _send_gotify(notcfg.get("gotify", {}), title, message, priority)
    if provider == "ntfy":
        return _send_ntfy(notcfg.get("ntfy", {}), title, message, priority)
    log(f"Unknown notification provider '{provider}'; skipping.")
    return False


def run_prune_job(origin: str = "unknown", wait: bool = False) -> bool:
    # Ensure we have the latest config before running prune job
    load_config(silent=True)
    
    lock = FileLock(str(LOCK_FILE))
    acquired = False
    try:
        if wait:
            # Try fast path first
            try:
                lock.acquire(timeout=0)
                acquired = True
                log(f"{origin.capitalize()} trigger: acquired prune lock.")
            except Timeout:
                log(f"{origin.capitalize()} trigger: waiting for any running prune to finish…")
                try:
                    lock.acquire(timeout=300)
                    acquired = True
                except Timeout:
                    log(f"{origin.capitalize()} trigger: waited 300s; skipping run.")
                    return False
        else:
            try:
                lock.acquire(timeout=0)
                acquired = True
            except Timeout:
                log(f"{origin.capitalize()} trigger: prune already in progress; skipping.")
                return False

        log("Starting prune job with configuration:")
        log(str(_redact_for_log(effective_config())))

        if not any([
            config.get("prune_containers"),
            config.get("prune_images"),
            config.get("prune_networks"),
            config.get("prune_volumes"),
        ]):
            log("No prune options selected. Job skipped.")
            return False

        if docker is None:
            log("Docker SDK not available; aborting prune.")
            return False

        client = None
        try:
            client = docker.from_env()
        except Exception as e:
            log(f"Failed to initialize Docker client: {e}. Aborting prune run.")
            return False

        containers_deleted = images_deleted = networks_deleted = volumes_deleted = 0
        total_space_reclaimed = 0

        # Containers
        if config.get("prune_containers"):
            try:
                log("Pruning containers…")
                r = client.containers.prune()
                log(f"Containers prune result: {r}")
                containers_deleted = len(r.get("ContainersDeleted") or [])
                total_space_reclaimed += int(r.get("SpaceReclaimed") or 0)
            except Exception as e:
                log(f"Error pruning containers: {e}")

        # Images
        if config.get("prune_images"):
            try:
                log("Pruning images (all unused)…")
                r = client.images.prune(filters={"dangling": False})
                log(f"Images prune result: {r}")
                deleted_list = r.get("ImagesDeleted") or []
                images_deleted = len(deleted_list)
                total_space_reclaimed += int(r.get("SpaceReclaimed") or 0)
            except Exception as e:
                log(f"Error pruning images: {e}")

        # Networks
        if config.get("prune_networks"):
            try:
                log("Pruning networks…")
                r = client.networks.prune()
                log(f"Networks prune result: {r}")
                networks_deleted = len(r.get("NetworksDeleted") or [])
            except Exception as e:
                log(f"Error pruning networks: {e}")

        # Volumes
        if config.get("prune_volumes"):
            try:
                log("Pruning volumes…")
                r = client.volumes.prune()
                log(f"Volumes prune result: {r}")
                volumes_deleted = len(r.get("VolumesDeleted") or [])
                total_space_reclaimed += int(r.get("SpaceReclaimed") or 0)
            except Exception as e:
                log(f"Error pruning volumes: {e}")

        log("Prune job finished.")

        anything_deleted = any([
            containers_deleted, images_deleted, networks_deleted,
            volumes_deleted, total_space_reclaimed > 0
        ])

        # Respect only_on_changes
        if not anything_deleted and config.get("notifications", {}).get("only_on_changes", True):
            log("Nothing was pruned; skipping notification.")
            return True

        # Build notification summary
        summary_lines = [
            f"Schedule: {describe_schedule()}",
            "",
            f"Containers deleted: {containers_deleted}",
            f"Images deleted:     {images_deleted}",
            f"Networks deleted:   {networks_deleted}",
            f"Volumes deleted:    {volumes_deleted}",
            f"Total space reclaimed: {human_bytes(total_space_reclaimed) if total_space_reclaimed else '0 B'}",
        ]
        if not anything_deleted:
            summary_lines.append("")
            summary_lines.append("Nothing to prune this run.")

        message = "\n".join(summary_lines)
        send_notification("PruneMate run completed", message)
        return True
    
    finally:
        if acquired:
            try:
                lock.release()
            except Exception:
                pass
        try:
            if client is not None:
                client.close()
        except Exception:
            pass


def compute_run_key(now: datetime.datetime) -> str:
    """Generate a unique key for the current scheduled run.
    
    Includes the configured time so changing the schedule time allows a new run
    on the same day/week/month.
    """
    freq = config.get("frequency", "daily")
    time_str = config.get("time", "03:00")
    date_str = now.date().isoformat()
    if freq == "daily":
        return f"daily-{date_str}-{time_str}"
    elif freq == "weekly":
        year, week, _ = now.isocalendar()
        return f"weekly-{year}-W{week}-{time_str}"
    elif freq == "monthly":
        return f"monthly-{now.year}-{now.month}-{time_str}"
    else:
        return f"daily-{date_str}-{time_str}"


def check_and_run_scheduled_job():
    """Check if current time matches the configured schedule and trigger prune.

    Uses a file-based "last run key" so the same period is not executed twice
    across multiple processes. If another worker already ran the job for the
    current key, this instance will skip.
    """
    # Always reload config to ensure we have the latest schedule across workers
    load_config(silent=True)
    
    now = datetime.datetime.now(app_timezone)
    freq = config.get("frequency", "daily")
    try:
        time_str = config.get("time", "03:00")
        hour_cfg, minute_cfg = [int(x) for x in time_str.split(":", 1)]
    except Exception:
        hour_cfg, minute_cfg = 3, 0

    hour_now = now.hour
    minute_now = now.minute
    should_run = False

    if freq == "daily":
        if hour_now == hour_cfg and minute_now == minute_cfg:
            should_run = True
    elif freq == "weekly":
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        cfg_dow = day_map.get(config.get("day_of_week", "mon"), 0)
        if now.weekday() == cfg_dow and hour_now == hour_cfg and minute_now == minute_cfg:
            should_run = True
    elif freq == "monthly":
        try:
            dom_cfg = int(config.get("day_of_month", 1))
        except Exception:
            dom_cfg = 1
        dom_cfg = max(1, min(31, dom_cfg))
        if now.day == dom_cfg and hour_now == hour_cfg and minute_now == minute_cfg:
            should_run = True

    if not should_run:
        return

    key = compute_run_key(now)
    # First check in-memory cache
    if last_run_key["value"] == key:
        log(f"Scheduled job skipped: already ran for key '{key}' (in-memory check)")
        return
    # Cross-process read
    disk_key = _read_last_run_key()
    if disk_key == key:
        last_run_key["value"] = key
        log(f"Scheduled job skipped: already ran for key '{key}' (disk check)")
        return

    log(f"Scheduled time reached ({freq}) at {hour_now:02d}:{minute_now:02d}, running prune.")
    # Mark as ran (best-effort) before execution to avoid duplicate triggers
    last_run_key["value"] = key
    _write_last_run_key(key)
    ran = run_prune_job(origin="scheduled", wait=False)
    if not ran:
        # If job skipped due to lock, keep the key set to avoid stampeding
        pass


def heartbeat():
    log("Heartbeat: scheduler is alive.")
    check_and_run_scheduled_job()


@app.route("/")
def index():
    # Reload config to ensure we show the latest settings across workers
    load_config(silent=True)
    return render_template("index.html", config=config, timezone=tz_name, config_path=CONFIG_PATH, use_24h=use_24h_format)


@app.route("/update", methods=["POST"])
def update():
    # Reload config to get the latest state before applying changes
    load_config(silent=True)
    old_config = json.loads(json.dumps(config))

    frequency = request.form.get("frequency", "daily")
    time_value = request.form.get("time", "03:00")
    day_of_week = request.form.get("day_of_week", "mon")
    raw_dom = request.form.get("day_of_month", "1")
    # Sanitize day-of-month (1..31)
    try:
        day_of_month = int(raw_dom)
    except Exception:
        day_of_month = 1
    day_of_month = max(1, min(31, day_of_month))

    prune_containers = bool(request.form.get("prune_containers"))
    prune_images = bool(request.form.get("prune_images"))
    prune_networks = bool(request.form.get("prune_networks"))
    prune_volumes = bool(request.form.get("prune_volumes"))

    provider = request.form.get("notifications_provider", "gotify")
    gotify_enabled = bool(request.form.get("gotify_enabled"))
    gotify_url = (request.form.get("gotify_url") or "").strip()
    gotify_token = (request.form.get("gotify_token") or "").strip()
    ntfy_enabled = bool(request.form.get("ntfy_enabled"))
    ntfy_url = (request.form.get("ntfy_url") or "").strip()
    ntfy_topic = (request.form.get("ntfy_topic") or "").strip()
    only_on_changes = bool(request.form.get("notifications_only_on_changes"))

    # Auto-enable gekozen provider indien velden ingevuld maar toggle vergeten
    if provider == "gotify" and not gotify_enabled and gotify_url and gotify_token:
        gotify_enabled = True
    if provider == "ntfy" and not ntfy_enabled and ntfy_url and ntfy_topic:
        ntfy_enabled = True

    # Validate HH:MM time; clamp to valid 24h range on parse errors
    def _validate_time(s: str) -> str:
        try:
            parts = s.split(":", 1)
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            h, m = 3, 0
        h = max(0, min(23, h))
        m = max(0, min(59, m))
        return f"{h:02d}:{m:02d}"

    time_value = _validate_time(time_value)

    new_values = {
        "frequency": frequency,
        "time": time_value,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "prune_containers": prune_containers,
        "prune_images": prune_images,
        "prune_networks": prune_networks,
        "prune_volumes": prune_volumes,
        "notifications": {
            "provider": provider,
            "gotify": {"enabled": gotify_enabled, "url": gotify_url, "token": gotify_token},
            "ntfy": {"enabled": ntfy_enabled, "url": ntfy_url, "topic": ntfy_topic},
            "only_on_changes": only_on_changes,
        },
    }

    schedule_keys = [
        "frequency","time","day_of_week","day_of_month",
        "prune_containers","prune_images","prune_networks","prune_volumes"
    ]
    schedule_changed = any(new_values[k] != old_config.get(k) for k in schedule_keys)
    config.update(new_values)
    if schedule_changed:
        # Clear last-run key so the next scheduled window can fire
        _clear_last_run_key()

    save_config()
    flash("Configuration updated.", "success")
    return redirect(url_for("index"))


@app.route("/run-now", methods=["POST"])
def run_now():
    # Reload config to use the latest prune settings
    load_config(silent=True)
    log("Manual run trigger received.")
    ran = run_prune_job(origin="manual", wait=True)
    flash("Prune job executed manually." if ran else "Prune job skipped (busy or timeout).", "info")
    return redirect(url_for("index"))


@app.route("/test-notification", methods=["POST"])
def test_notification():
    # First save the config with the current form data, then test notification
    load_config(silent=True)
    old_config = json.loads(json.dumps(config))

    frequency = request.form.get("frequency", "daily")
    time_value = request.form.get("time", "03:00")
    day_of_week = request.form.get("day_of_week", "mon")
    raw_dom = request.form.get("day_of_month", "1")
    try:
        day_of_month = int(raw_dom)
    except Exception:
        day_of_month = 1
    day_of_month = max(1, min(31, day_of_month))

    prune_containers = bool(request.form.get("prune_containers"))
    prune_images = bool(request.form.get("prune_images"))
    prune_networks = bool(request.form.get("prune_networks"))
    prune_volumes = bool(request.form.get("prune_volumes"))

    provider = request.form.get("notifications_provider", "gotify")
    gotify_enabled = bool(request.form.get("gotify_enabled"))
    gotify_url = (request.form.get("gotify_url") or "").strip()
    gotify_token = (request.form.get("gotify_token") or "").strip()
    ntfy_enabled = bool(request.form.get("ntfy_enabled"))
    ntfy_url = (request.form.get("ntfy_url") or "").strip()
    ntfy_topic = (request.form.get("ntfy_topic") or "").strip()
    only_on_changes = bool(request.form.get("notifications_only_on_changes"))

    # Auto-enable gekozen provider indien velden ingevuld maar toggle vergeten
    if provider == "gotify" and not gotify_enabled and gotify_url and gotify_token:
        gotify_enabled = True
    if provider == "ntfy" and not ntfy_enabled and ntfy_url and ntfy_topic:
        ntfy_enabled = True

    def _validate_time(s: str) -> str:
        try:
            parts = s.split(":", 1)
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            h, m = 3, 0
        h = max(0, min(23, h))
        m = max(0, min(59, m))
        return f"{h:02d}:{m:02d}"

    time_value = _validate_time(time_value)

    new_values = {
        "frequency": frequency,
        "time": time_value,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "prune_containers": prune_containers,
        "prune_images": prune_images,
        "prune_networks": prune_networks,
        "prune_volumes": prune_volumes,
        "notifications": {
            "provider": provider,
            "gotify": {"enabled": gotify_enabled, "url": gotify_url, "token": gotify_token},
            "ntfy": {"enabled": ntfy_enabled, "url": ntfy_url, "topic": ntfy_topic},
            "only_on_changes": only_on_changes,
        },
    }

    schedule_keys = [
        "frequency","time","day_of_week","day_of_month",
        "prune_containers","prune_images","prune_networks","prune_volumes"
    ]
    schedule_changed = any(new_values[k] != old_config.get(k) for k in schedule_keys)
    config.update(new_values)
    if schedule_changed:
        _clear_last_run_key()

    save_config()
    
    # Now test the notification with the saved config
    log("Notification test requested from UI.")
    ok = send_notification(
        "PruneMate test notification",
        "This is a test message from PruneMate.\n\nIf you see this, your current provider settings are working.",
        priority=3,
    )
    flash("Configuration saved. " + ("Test notification sent." if ok else "Test notification failed (check settings & logs)."), "info")
    return redirect(url_for("index"))


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    load_config()
    scheduler.add_job(heartbeat, CronTrigger(second=0), id="heartbeat", max_instances=1, coalesce=True)
    log("Scheduler heartbeat job started (every minute at :00).")
    
    options = {
        "bind": "0.0.0.0:8080",
        "workers": 1,
        "threads": 2,
        "timeout": 120,
        # Disable access logs (those 172.x request lines)
        "accesslog": None,
        "errorlog": "-",
        "loglevel": "info",
    }
    StandaloneApplication(app, options).run()
