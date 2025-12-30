"""PruneMate - Docker定时清理助手

功能特性：
1. 支持定时清理Docker资源
2. 可清理：容器、镜像、网络、卷、构建缓存
3. 支持多Docker主机
4. 通知集成：Gotify、ntfy、Discord、Telegram
5. 历史统计与预览功能
"""

import os
import sys
import json
import logging
import tempfile
import datetime
import calendar
import base64
import urllib.request
import urllib.parse
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from filelock import FileLock, Timeout
from gunicorn.app.base import BaseApplication
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

# 可选Docker导入（最佳尝试）
try:
    import docker
except Exception:
    docker = None

# Flask应用初始化
app = Flask(__name__)
app.secret_key = os.environ.get("PRUNEMATE_SECRET", "prunemate-secret-key")

# 路径和默认配置
CONFIG_PATH = Path(os.environ.get("PRUNEMATE_CONFIG", "/config/config.json"))
# 文件锁：确保跨进程的清理任务不会同时执行
LOCK_FILE = Path(os.environ.get("PRUNEMATE_LOCK", "/config/prunemate.lock"))
# 用于记录上次运行时间的文件，防止多Worker重复执行
LAST_RUN_FILE = Path(os.environ.get("PRUNEMATE_LAST_RUN", "/config/last_run_key"))
LAST_RUN_LOCK = Path(str(LAST_RUN_FILE) + ".lock")
# 用于保存历史统计数据的文件
STATS_FILE = Path(os.environ.get("PRUNEMATE_STATS", "/config/stats.json"))

DEFAULT_CONFIG = {
    "schedule_enabled": True,
    "frequency": "daily",
    "time": "03:00",
    "day_of_week": "mon",
    "day_of_month": 1,
    "prune_containers": False,
    "prune_images": True,
    "prune_networks": False,
    "prune_volumes": False,
    "prune_build_cache": False,
    "docker_hosts": [],
    "notifications": {
        "provider": "gotify",
        "gotify": {"enabled": False, "url": "", "token": ""},
        "ntfy": {"enabled": False, "url": "", "topic": "", "token": ""},
        "discord": {"enabled": False, "webhook_url": ""},
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
        "priority": "medium",
        "only_on_changes": True,
    },
}

# 配置字典，初始化为默认配置
config = json.loads(json.dumps(DEFAULT_CONFIG))
# 配置读写锁，确保多Worker线程安全
import threading
config_lock = threading.RLock()
# 内存缓存上次运行时间
last_run_key = {"value": None}

# ---- CLI工具处理 ----
if len(sys.argv) > 1 and sys.argv[1] == "--gen-hash":
    if len(sys.argv) > 2:
        password = sys.argv[2]
        # 生成密码哈希
        raw_hash = generate_password_hash(password)
        safe_hash = base64.b64encode(raw_hash.encode("utf-8")).decode("utf-8")
        print(safe_hash)
        sys.exit(0)
    else:
        print("用法: python prunemate.py --gen-hash <密码>")
        sys.exit(1)


def configure_logging():
    """配置日志记录，支持控制台和文件滚动日志"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)
    try:
        Path("/var/log").mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler("/var/log/prunemate.log", maxBytes=5_000_000, backupCount=3)
        fh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(fh)
    except Exception:
        logger.exception("文件日志配置失败；仅使用控制台日志继续运行。")


configure_logging()


# 时区配置
tz_name = os.environ.get("PRUNEMATE_TZ", "UTC")
try:
    app_timezone = ZoneInfo(tz_name)
except Exception:
    logging.warning("时区 '%s' 无效，回退到UTC", tz_name)
    app_timezone = ZoneInfo("UTC")

logging.info("使用时区: %s", app_timezone)

# 时间格式（12小时制或24小时制）
use_24h_format = os.environ.get("PRUNEMATE_TIME_24H", "true").lower() in ("true", "1", "yes")
logging.info("使用时间格式: %s", "24小时制" if use_24h_format else "12小时制")

# 抑制APScheduler冗长的任务执行日志
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

# 调度器初始化
# 后台调度器用于每分钟心跳检查，实际任务在__main__中添加
scheduler = BackgroundScheduler(
    timezone=app_timezone,
    job_defaults={
        "coalesce": False,
        "misfire_grace_time": 300,
    },
)
scheduler.start()


def log(message: str):
    """带时区时间戳的日志记录"""
    now = datetime.datetime.now(app_timezone)
    timestamp = now.isoformat(timespec="seconds")
    logging.info("[%s] %s", timestamp, message)


def _redact_for_log(obj):
    """递归清理日志中的敏感信息"""
    if isinstance(obj, dict):
        redacted = {}
        for k, v in obj.items():
            if k.lower() in {"token", "api_key", "apikey", "password", "secret"}:
                redacted[k] = "***"
            elif k.lower() == "url" and isinstance(v, str):
                # 清理URL中的用户名和密码
                parsed = urllib.parse.urlparse(v)
                if parsed.username or parsed.password:
                    clean_url = urllib.parse.urlunparse((
                        parsed.scheme,
                        f"***:***@{parsed.hostname}" + (f":{parsed.port}" if parsed.port else ""),
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment
                    ))
                    redacted[k] = clean_url
                else:
                    redacted[k] = v
            else:
                redacted[k] = _redact_for_log(v)
        return redacted
    if isinstance(obj, list):
        return [_redact_for_log(x) for x in obj]
    return obj


# ---- 跨进程的上次运行时间管理 ----
def _read_last_run_key() -> str | None:
    """从磁盘读取上次运行时间"""
    try:
        with FileLock(str(LAST_RUN_LOCK)):
            if LAST_RUN_FILE.exists():
                return LAST_RUN_FILE.read_text(encoding="utf-8").strip() or None
    except Exception:
        # 读取失败时回退到内存缓存
        pass
    return None


def _write_last_run_key(key: str) -> None:
    """将上次运行时间写入磁盘"""
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
        # 写入失败时回退到内存缓存
        pass


def _clear_last_run_key() -> None:
    """清除内存和磁盘上的上次运行时间记录"""
    last_run_key["value"] = None
    try:
        with FileLock(str(LAST_RUN_LOCK)):
            if LAST_RUN_FILE.exists():
                LAST_RUN_FILE.unlink()
    except Exception:
        pass


# ---- 历史统计数据管理 ----
def load_stats() -> dict:
    """从磁盘加载历史统计数据"""
    default_stats = {
        "total_space_reclaimed": 0,
        "containers_deleted": 0,
        "images_deleted": 0,
        "networks_deleted": 0,
        "volumes_deleted": 0,
        "build_cache_deleted": 0,
        "prune_runs": 0,
        "first_run": None,
        "last_run": None,
    }
    
    try:
        if STATS_FILE.exists():
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                loaded_stats = json.load(f)
            
            merged_stats = json.loads(json.dumps(default_stats))
            for key in default_stats:
                if key in loaded_stats:
                    if key in {"total_space_reclaimed", "containers_deleted", "images_deleted", 
                              "networks_deleted", "volumes_deleted", "build_cache_deleted", "prune_runs"}:
                        try:
                            merged_stats[key] = int(loaded_stats[key])
                        except (ValueError, TypeError):
                            log(f"统计字段 '{key}' 类型无效，使用默认值: 0")
                            merged_stats[key] = 0
                    else:
                        merged_stats[key] = loaded_stats[key]
            
            return merged_stats
    except json.JSONDecodeError as e:
        log(f"统计文件损坏（无效JSON）: {e}。使用默认配置，下次保存将覆盖。")
    except Exception as e:
        log(f"从 {STATS_FILE} 加载统计数据时出错: {e}")
    
    return json.loads(json.dumps(default_stats))


def save_stats(stats: dict) -> None:
    """原子化保存统计数据到磁盘"""
    try:
        parent = STATS_FILE.parent
        parent.mkdir(parents=True, exist_ok=True)
        
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, dir=str(parent), encoding="utf-8") as tmp:
                json.dump(stats, tmp, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = Path(tmp.name)
            
            try:
                tmp_path.chmod(0o600)
            except Exception:
                pass
            
            tmp_path.replace(STATS_FILE)
            log(f"统计数据已保存到 {STATS_FILE}")
        except Exception:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise
    except Exception as e:
        log(f"保存统计数据时出错: {e}")


def update_stats(containers: int, images: int, networks: int, volumes: int, build_cache: int, space: int) -> None:
    """更新历史统计数据"""
    stats = load_stats()
    
    try:
        stats["containers_deleted"] = int(stats.get("containers_deleted") or 0) + int(containers or 0)
        stats["images_deleted"] = int(stats.get("images_deleted") or 0) + int(images or 0)
        stats["networks_deleted"] = int(stats.get("networks_deleted") or 0) + int(networks or 0)
        stats["volumes_deleted"] = int(stats.get("volumes_deleted") or 0) + int(volumes or 0)
        stats["build_cache_deleted"] = int(stats.get("build_cache_deleted") or 0) + int(build_cache or 0)
        stats["total_space_reclaimed"] = int(stats.get("total_space_reclaimed") or 0) + int(space or 0)
        stats["prune_runs"] = int(stats.get("prune_runs") or 0) + 1
    except (ValueError, TypeError) as e:
        log(f"统计数据更新时类型错误: {e}。统计数据可能不完整。")
    
    now = datetime.datetime.now(app_timezone).isoformat()
    if stats.get("first_run") is None:
        stats["first_run"] = now
    stats["last_run"] = now
    
    save_stats(stats)


def human_bytes(num: int) -> str:
    """将字节数转换为人类可读的格式（B, KB, MB, GB, TB, PB）"""
    n = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def format_time(time_str: str) -> str:
    """根据用户偏好格式化时间字符串"""
    if use_24h_format:
        return time_str
    # 将24小时格式转换为12小时格式
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = parts[1] if len(parts) > 1 else "00"
        
        if hour == 0:
            return f"12:{minute} 上午"
        elif hour < 12:
            return f"{hour}:{minute} 上午"
        elif hour == 12:
            return f"12:{minute} 下午"
        else:
            return f"{hour - 12}:{minute} 下午"
    except Exception:
        return time_str


def describe_schedule() -> str:
    """生成当前计划任务的人类可读描述"""
    freq = config.get("frequency", "daily")
    time_str = config.get("time", "03:00")
    formatted_time = format_time(time_str)
    if freq == "daily":
        return f"每日 {formatted_time} ({tz_name})"
    if freq == "weekly":
        day_key = config.get("day_of_week", "mon")
        day_names = {
            "mon": "周一", "tue": "周二", "wed": "周三",
            "thu": "周四", "fri": "周五", "sat": "周六", "sun": "周日",
        }
        return f"每周 {day_names.get(day_key, day_key)} {formatted_time} ({tz_name})"
    if freq == "monthly":
        day_of_month = config.get("day_of_month", 1)
        return f"每月 {day_of_month} 日 {formatted_time} ({tz_name})"
    return f"{freq} {formatted_time} ({tz_name})"


def validate_time(s: str) -> str:
    """验证时间格式，确保为HH:MM格式"""
    try:
        parts = s.split(":", 1)
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
    except Exception as e:
        log(f"时间格式 '{s}' 无效: {e}。回退到 03:00")
        h, m = 3, 0
    h = max(0, min(23, h))
    m = max(0, min(59, m))
    return f"{h:02d}:{m:02d}"


def _deep_merge(base: dict, override: dict) -> None:
    """深度合并两个字典"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def effective_config():
    """返回当前有效的配置"""
    freq = config.get("frequency", "daily")
    base = {
        "schedule_enabled": config.get("schedule_enabled", True),
        "frequency": freq,
        "time": config.get("time"),
        "prune_containers": config.get("prune_containers"),
        "prune_images": config.get("prune_images"),
        "prune_networks": config.get("prune_networks"),
        "prune_volumes": config.get("prune_volumes"),
        "prune_build_cache": config.get("prune_build_cache"),
        "docker_hosts": config.get("docker_hosts"),
        "notifications": config.get("notifications"),
    }
    if freq == "weekly":
        base["day_of_week"] = config.get("day_of_week")
    elif freq == "monthly":
        base["day_of_month"] = config.get("day_of_month")
    return base


def load_config(silent=False):
    """从磁盘加载配置文件"""
    global config
    with config_lock:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            _deep_merge(merged, data)

            # 迁移旧版通知配置
            if "notifications" not in data:
                has_gotify_keys = any(k in data for k in ("gotify_enabled", "gotify_url", "gotify_token"))
                has_ntfy_keys = any(k in data for k in ("ntfy_enabled", "ntfy_url", "ntfy_topic", "ntfy_token"))
                has_discord_keys = any(k in data for k in ("discord_enabled", "discord_webhook_url"))
                
                if has_gotify_keys or has_ntfy_keys or has_discord_keys:
                    if "notifications" not in merged:
                        merged["notifications"] = json.loads(json.dumps(DEFAULT_CONFIG["notifications"]))
                    
                    if has_gotify_keys:
                        got = {
                            "enabled": bool(data.get("gotify_enabled")),
                            "url": (data.get("gotify_url") or "").strip(),
                            "token": (data.get("gotify_token") or "").strip(),
                        }
                        merged["notifications"]["gotify"] = got
                    
                    if has_ntfy_keys:
                        ntf = {
                            "enabled": bool(data.get("ntfy_enabled")),
                            "url": (data.get("ntfy_url") or "").strip(),
                            "topic": (data.get("ntfy_topic") or "").strip(),
                            "token": (data.get("ntfy_token") or "").strip(),
                        }
                        merged["notifications"]["ntfy"] = ntf
                    
                    if has_discord_keys:
                        disc = {
                            "enabled": bool(data.get("discord_enabled")),
                            "webhook_url": (data.get("discord_webhook_url") or "").strip(),
                        }
                        merged["notifications"]["discord"] = disc
                    
                    if has_discord_keys and data.get("discord_enabled"):
                        merged["notifications"]["provider"] = "discord"
                    elif has_ntfy_keys and data.get("ntfy_enabled"):
                        merged["notifications"]["provider"] = "ntfy"
                    elif has_gotify_keys:
                        merged["notifications"]["provider"] = "gotify"
                    
                    if "gotify_only_on_changes" in data:
                        merged["notifications"]["only_on_changes"] = bool(data["gotify_only_on_changes"])
                    elif "ntfy_only_on_changes" in data:
                        merged["notifications"]["only_on_changes"] = bool(data["ntfy_only_on_changes"])
            
            if "notifications" not in merged:
                merged["notifications"] = json.loads(json.dumps(DEFAULT_CONFIG["notifications"]))
            
            # 确保所有通知提供商的配置都存在
            for provider_key in ["gotify", "ntfy", "discord", "telegram"]:
                if provider_key not in merged["notifications"]:
                    merged["notifications"]["provider_key"] = json.loads(json.dumps(DEFAULT_CONFIG["notifications"][provider_key]))
            
            # 迁移数字优先级到文本优先级
            priority = merged.get("notifications", {}).get("priority")
            if isinstance(priority, int):
                if priority <= 3:
                    merged["notifications"]["priority"] = "low"
                elif priority <= 7:
                    merged["notifications"]["priority"] = "medium"
                else:
                    merged["notifications"]["priority"] = "high"
            elif not isinstance(priority, str) or priority not in ["low", "medium", "high"]:
                merged["notifications"]["priority"] = "medium"
            
            if "docker_hosts" not in merged or not isinstance(merged["docker_hosts"], list):
                merged["docker_hosts"] = json.loads(json.dumps(DEFAULT_CONFIG["docker_hosts"]))
            # 清理本地Docker主机记录
            merged["docker_hosts"] = [
                h for h in merged["docker_hosts"]
                if h.get("name") != "Local" and "unix://" not in h.get("url", "")
            ]
            # 验证每个主机的必填字段
            for host in merged["docker_hosts"]:
                if "name" not in host:
                    host["name"] = "未命名"
                if "url" not in host:
                    host["url"] = "tcp://localhost:2375"
                if "enabled" not in host:
                    host["enabled"] = True

            config = merged
            if not silent:
                log(f"从 {CONFIG_PATH} 加载配置: {_redact_for_log(effective_config())}")
        except FileNotFoundError:
            if not silent:
                log(f"未找到配置文件 {CONFIG_PATH}，使用默认配置。")
            config = json.loads(json.dumps(DEFAULT_CONFIG))
        except Exception as e:
            if not silent:
                log(f"从 {CONFIG_PATH} 加载配置时出错: {e}。使用默认配置。")
            config = json.loads(json.dumps(DEFAULT_CONFIG))


def save_config():
    """原子化保存配置到磁盘"""
    with config_lock:
        try:
            path = Path(CONFIG_PATH)
            parent = path.parent or Path(".")
            parent.mkdir(parents=True, exist_ok=True)

            config_to_save = json.loads(json.dumps(config))
            if "docker_hosts" in config_to_save:
                config_to_save["docker_hosts"] = [
                    h for h in config_to_save["docker_hosts"]
                    if h.get("name") != "Local" and "unix://" not in h.get("url", "")
                ]

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile("w", delete=False, dir=str(parent), encoding="utf-8") as tmp:
                    json.dump(config_to_save, tmp, indent=2)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    tmp_path = Path(tmp.name)
                try:
                    tmp_path.chmod(0o600)
                except Exception:
                    pass
                tmp_path.replace(path)
                log(f"配置已保存到 {path}: {_redact_for_log(config_to_save)}")
            finally:
                if tmp_path and tmp_path.exists() and tmp_path != path:
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
        except Exception as e:
            log(f"保存配置到 {CONFIG_PATH} 时失败: {e}")


def _send_gotify(cfg: dict, title: str, message: str, priority: str = "medium") -> bool:
    """通过Gotify发送通知"""
    if not cfg.get("enabled"):
        log("Gotify已禁用；跳过通知。")
        return False
    url = (cfg.get("url") or "").strip()
    token = (cfg.get("token") or "").strip()
    if not url or not token:
        log("Gotify已启用但URL或令牌缺失；跳过。")
        return False
    
    priority_map = {"low": 2, "medium": 5, "high": 8}
    gotify_priority = priority_map.get(priority, 2)
    
    endpoint = url.rstrip("/") + "/message?token=" + token
    payload = json.dumps({"title": title, "message": message, "priority": gotify_priority}).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            log(f"Gotify通知已发送，状态={getattr(resp, 'status', '?')}")
            return True
    except Exception as e:
        log(f"发送Gotify通知失败: {e}")
        return False


def _send_ntfy(cfg: dict, title: str, message: str, priority: str = "medium") -> bool:
    """通过ntfy发送通知"""
    if not cfg.get("enabled"):
        log("ntfy已禁用；跳过通知。")
        return False
    url = (cfg.get("url") or "").strip()
    topic = (cfg.get("topic") or "").strip()
    token = (cfg.get("token") or "").strip()
    
    if not url or not topic:
        log("ntfy已启用但URL或主题缺失；跳过。")
        return False
    
    priority_map = {"low": 2, "medium": 3, "high": 5}
    ntfy_priority = priority_map.get(priority, 2)
    
    parsed = urllib.parse.urlparse(url)
    headers = {"Title": title, "Priority": str(ntfy_priority), "Content-Type": "text/plain"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        endpoint = url.rstrip("/") + "/" + topic.lstrip("/")
    elif parsed.username or parsed.password:
        clean_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        username = parsed.username or ""
        password = parsed.password or ""
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {encoded_credentials}"
        endpoint = clean_url.rstrip("/") + "/" + topic.lstrip("/")
    else:
        endpoint = url.rstrip("/") + "/" + topic.lstrip("/")
    
    payload = message.encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            log(f"ntfy通知已发送，状态={getattr(resp, 'status', '?')}")
            return True
    except Exception as e:
        log(f"发送ntfy通知失败: {e}")
        return False


def _send_discord(cfg: dict, title: str, message: str, priority: str = "medium") -> bool:
    """通过Discord Webhook发送通知"""
    if not cfg.get("enabled"):
        log("Discord已禁用；跳过通知。")
        return False
    webhook_url = (cfg.get("webhook_url") or "").strip()
    if not webhook_url:
        log("Discord已启用但Webhook URL缺失；跳过。")
        return False
    
    if not webhook_url.startswith("https://discord.com/api/webhooks/") and \
       not webhook_url.startswith("https://discordapp.com/api/webhooks/"):
        log(f"Discord Webhook URL格式无效: {webhook_url[:50]}...")
        return False
    
    color_map = {
        "low": 0x2ECC71,     # 绿色（信息）
        "medium": 0xF39C12,  # 橙色（警告）
        "high": 0xE74C3C,    # 红色（严重）
    }
    embed_color = color_map.get(priority, 0x2ECC71)
    
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": embed_color,
            "timestamp": datetime.datetime.now(app_timezone).isoformat()
        }]
    }
    
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PruneMate/1.3.0 (Docker清理助手)"
    }
    req = urllib.request.Request(webhook_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log(f"Discord通知已发送，状态={getattr(resp, 'status', '?')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        log(f"Discord Webhook HTTP错误 {e.code}: {e.reason}。响应体: {error_body[:200]}")
        return False
    except urllib.error.URLError as e:
        log(f"Discord Webhook网络错误: {e.reason}")
        return False
    except Exception as e:
        log(f"发送Discord通知失败: {e}")
        return False


def _send_telegram(cfg: dict, title: str, message: str, priority: str = "medium") -> bool:
    """通过Telegram Bot API发送通知"""
    if not cfg.get("enabled"):
        log("Telegram已禁用；跳过通知。")
        return False
    bot_token = (cfg.get("bot_token") or "").strip()
    chat_id = (cfg.get("chat_id") or "").strip()
    if not bot_token or not chat_id:
        log("Telegram已启用但bot_token或chat_id缺失；跳过。")
        return False
    
    disable_notification = (priority == "low")
    
    full_message = f"<b>{title}</b>\n\n{message}"
    
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = json.dumps({
        "chat_id": chat_id,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_notification": disable_notification
    }).encode("utf-8")
    
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PruneMate/1.3.0 (Docker清理助手)"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                log(f"Telegram通知已发送，消息ID={result.get('result', {}).get('message_id', '?')}")
                return True
            else:
                log(f"Telegram API返回ok=false: {result}")
                return False
    except Exception as e:
        log(f"发送Telegram通知失败: {e}")
        return False


def send_notification(title: str, message: str, priority: str = "medium") -> bool:
    """使用配置的通知提供商发送通知"""
    notcfg = config.get("notifications", DEFAULT_CONFIG["notifications"])
    provider = (notcfg.get("provider") or "gotify").lower()
    if provider == "gotify":
        return _send_gotify(notcfg.get("gotify", {}), title, message, priority)
    if provider == "ntfy":
        return _send_ntfy(notcfg.get("ntfy", {}), title, message, priority)
    if provider == "discord":
        return _send_discord(notcfg.get("discord", {}), title, message, priority)
    if provider == "telegram":
        return _send_telegram(notcfg.get("telegram", {}), title, message, priority)
    log(f"未知的通知提供商 '{provider}'; 跳过通知。")
    return False


def create_docker_client(host_url: str):
    """创建Docker客户端实例"""
    if docker is None:
        log("Docker SDK不可用。")
        return None
    
    try:
        if host_url.startswith("unix://"):
            return docker.DockerClient(base_url=host_url)
        elif host_url.startswith("tcp://") or host_url.startswith("http://") or host_url.startswith("https://"):
            return docker.DockerClient(base_url=host_url)
        else:
            return docker.DockerClient(base_url=host_url)
    except Exception as e:
        log(f"为 {host_url} 创建Docker客户端失败: {e}")
        return None


def get_prune_preview() -> dict:
    """获取清理预览，不实际执行清理"""
    load_config(silent=True)
    
    if not any([
        config.get("prune_containers"),
        config.get("prune_images"),
        config.get("prune_networks"),
        config.get("prune_volumes"),
        config.get("prune_build_cache"),
    ]):
        return {"error": "未选择任何清理选项", "hosts": []}
    
    if docker is None:
        return {"error": "Docker SDK不可用", "hosts": []}
    
    docker_hosts = config.get("docker_hosts", [])
    enabled_external_hosts = [
        h for h in docker_hosts 
        if h.get("enabled", True) and h.get("name") != "Local" and "unix://" not in h.get("url", "")
    ]
    
    all_hosts = [
        {"name": "本地", "url": "unix:///var/run/docker.sock", "enabled": True}
    ] + enabled_external_hosts
    
    preview_results = []
    total_containers = 0
    total_images = 0
    total_networks = 0
    total_volumes = 0
    total_build_cache = 0
    
    for host in all_hosts:
        host_name = host.get("name", "未命名")
        host_url = host.get("url", "unix:///var/run/docker.sock")
        
        client = None
        try:
            client = create_docker_client(host_url)
            if client is None:
                preview_results.append({
                    "name": host_name,
                    "url": host_url,
                    "success": False,
                    "error": "连接失败",
                    "containers": [],
                    "images": [],
                    "networks": [],
                    "volumes": [],
                    "build_cache": []
                })
                continue
            
            containers_list = []
            images_list = []
            networks_list = []
            volumes_list = []
            build_cache_list = []
            
            if config.get("prune_containers"):
                try:
                    all_containers = client.containers.list(all=True)
                    stopped_containers = [c for c in all_containers if c.status in ["exited", "dead", "created"]]
                    containers_list = [
                        {"id": c.short_id, "name": c.name, "status": c.status}
                        for c in stopped_containers
                    ]
                except Exception as e:
                    log(f"[{host_name}] 列出容器时出错: {e}")
            
            if config.get("prune_images"):
                try:
                    all_images = client.images.list()
                    used_image_ids = set()
                    for container in client.containers.list(all=True):
                        img_id = container.attrs.get("Image")
                        if img_id:
                            used_image_ids.add(img_id)
                    
                    unused_images = [img for img in all_images if img.id not in used_image_ids]
                    images_list = [
                        {
                            "id": img.short_id,
                            "tags": img.tags[:3] if img.tags else ["<none>"],
                            "size": human_bytes(img.attrs.get("Size", 0))
                        }
                        for img in unused_images
                    ]
                except Exception as e:
                    log(f"[{host_name}] 列出镜像时出错: {e}")
            
            if config.get("prune_networks"):
                try:
                    networks = client.networks.list()
                    unused_networks = []
                    
                    running_network_ids = set()
                    for container in client.containers.list(filters={"status": "running"}):
                        network_settings = container.attrs.get("NetworkSettings", {}).get("Networks", {})
                        for net_name, net_info in network_settings.items():
                            if net_info.get("NetworkID"):
                                running_network_ids.add(net_info["NetworkID"])
                    
                    for net in networks:
                        if net.name in ["bridge", "host", "none"]:
                            continue
                        if net.id in running_network_ids:
                            continue
                        unused_networks.append(net)
                    
                    networks_list = [
                        {"id": net.short_id, "name": net.name}
                        for net in unused_networks
                    ]
                except Exception as e:
                    log(f"[{host_name}] 列出网络时出错: {e}")
            
            if config.get("prune_volumes"):
                try:
                    all_volumes_result = client.volumes.list()
                    all_volumes = all_volumes_result if all_volumes_result else []
                    used_volume_names = set()
                    for container in client.containers.list(all=True):
                        for mount in container.attrs.get("Mounts", []):
                            if mount.get("Type") == "volume":
                                used_volume_names.add(mount.get("Name"))
                    
                    unused_volumes = [v for v in all_volumes if v.name not in used_volume_names]
                    volumes_list = [
                        {"name": v.name, "driver": v.attrs.get("Driver", "local")}
                        for v in unused_volumes
                    ]
                except Exception as e:
                    log(f"[{host_name}] 列出卷时出错: {e}")
            
            if config.get("prune_build_cache"):
                try:
                    df_result = client.api.df()
                    build_cache_info = df_result.get("BuildCache", [])
                    
                    reclaimable_cache = []
                    for c in build_cache_info:
                        if "Reclaimable" in c:
                            if c["Reclaimable"]:
                                reclaimable_cache.append(c)
                        elif not c.get("InUse", False):
                            reclaimable_cache.append(c)
                    
                    build_cache_list = [
                        {
                            "id": c.get("ID", "")[:12],
                            "type": c.get("Type", "unknown"),
                            "size": human_bytes(c.get("Size", 0)),
                            "reclaimable": c.get("Reclaimable", True),
                            "inUse": c.get("InUse", False)
                        }
                        for c in reclaimable_cache
                    ]
                    
                    if build_cache_list:
                        log(f"[{host_name}] 预览发现 {len(build_cache_list)} 个可回收的构建缓存条目")
                except Exception as e:
                    log(f"[{host_name}] 列出构建缓存时出错: {e}")
            
            total_containers += len(containers_list)
            total_images += len(images_list)
            total_networks += len(networks_list)
            total_volumes += len(volumes_list)
            total_build_cache += len(build_cache_list)
            
            preview_results.append({
                "name": host_name,
                "url": host_url,
                "success": True,
                "containers": containers_list,
                "images": images_list,
                "networks": networks_list,
                "volumes": volumes_list,
                "build_cache": build_cache_list,
                "totals": {
                    "containers": len(containers_list),
                    "images": len(images_list),
                    "networks": len(networks_list),
                    "volumes": len(volumes_list),
                    "build_cache": len(build_cache_list)
                }
            })
            
        except Exception as e:
            log(f"[{host_name}] 获取预览时出错: {e}")
            preview_results.append({
                "name": host_name,
                "url": host_url,
                "success": False,
                "error": str(e),
                "containers": [],
                "images": [],
                "networks": [],
                "volumes": [],
                "build_cache": []
            })
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
    
    return {
        "hosts": preview_results,
        "totals": {
            "containers": total_containers,
            "images": total_images,
            "networks": total_networks,
            "volumes": total_volumes,
            "build_cache": total_build_cache
        }
    }


def run_prune_job(origin: str = "unknown", wait: bool = False) -> bool:
    """执行Docker清理任务"""
    load_config(silent=True)
    
    lock = FileLock(str(LOCK_FILE))
    acquired = False
    try:
        if wait:
            try:
                lock.acquire(timeout=0)
                acquired = True
                log(f"{origin.capitalize()} 触发: 已获取清理锁。")
            except Timeout:
                log(f"{origin.capitalize()} 触发: 等待正在运行的清理任务完成…")
                try:
                    lock.acquire(timeout=300)
                    acquired = True
                except Timeout:
                    log(f"{origin.capitalize()} 触发: 已等待300秒; 跳过本次运行。")
                    return False
        else:
            try:
                lock.acquire(timeout=0)
                acquired = True
            except Timeout:
                log(f"{origin.capitalize()} 触发: 清理任务已在进行中; 跳过本次运行。")
                return False

        log("开始清理任务，配置如下:")
        log(str(_redact_for_log(effective_config())))

        if not any([
            config.get("prune_containers"),
            config.get("prune_images"),
            config.get("prune_networks"),
            config.get("prune_volumes"),
            config.get("prune_build_cache"),
        ]):
            log("未选择任何清理选项。任务跳过。")
            return False

        if docker is None:
            log("Docker SDK不可用; 终止清理任务。")
            return False

        docker_hosts = config.get("docker_hosts", [])
        enabled_external_hosts = [
            h for h in docker_hosts 
            if h.get("enabled", True) and h.get("name") != "Local" and "unix://" not in h.get("url", "")
        ]
        
        all_hosts = [
            {"name": "本地", "url": "unix:///var/run/docker.sock", "enabled": True}
        ] + enabled_external_hosts
        
        log(f"处理 {len(all_hosts)} 个主机 (1个本地 + {len(enabled_external_hosts)} 个外部)...")
        
        total_containers_deleted = 0
        total_images_deleted = 0
        total_networks_deleted = 0
        total_volumes_deleted = 0
        total_build_cache_deleted = 0
        total_space_reclaimed = 0
        
        host_results = []
        
        for host in all_hosts:
            host_name = host.get("name", "未命名")
            host_url = host.get("url", "unix:///var/run/docker.sock")
            
            log(f"--- 处理主机: {host_name} ({host_url}) ---")
            
            client = None
            try:
                client = create_docker_client(host_url)
                if client is None:
                    log(f"无法连接到 {host_name}; 跳过此主机。")
                    host_results.append({
                        "name": host_name,
                        "url": host_url,
                        "success": False,
                        "error": "连接失败",
                        "containers": 0,
                        "images": 0,
                        "networks": 0,
                        "volumes": 0,
                        "build_cache": 0,
                        "space": 0,
                    })
                    continue
                
                containers_deleted = images_deleted = networks_deleted = volumes_deleted = build_cache_deleted = 0
                space_reclaimed = 0

                if config.get("prune_containers"):
                    try:
                        log(f"[{host_name}] 清理容器…")
                        r = client.containers.prune()
                        log(f"[{host_name}] 容器清理结果: {r}")
                        containers_deleted = len(r.get("ContainersDeleted") or [])
                        space_reclaimed += int(r.get("SpaceReclaimed") or 0)
                    except Exception as e:
                        log(f"[{host_name}] 清理容器时出错: {e}")

                if config.get("prune_images"):
                    try:
                        log(f"[{host_name}] 清理所有未使用的镜像…")
                        r = client.images.prune(filters={"dangling": False})
                        log(f"[{host_name}] 镜像清理结果: {r}")
                        deleted_list = r.get("ImagesDeleted") or []
                        images_deleted = len(deleted_list)
                        space_reclaimed += int(r.get("SpaceReclaimed") or 0)
                    except Exception as e:
                        log(f"[{host_name}] 清理镜像时出错: {e}")

                if config.get("prune_networks"):
                    try:
                        log(f"[{host_name}] 清理网络…")
                        r = client.networks.prune()
                        log(f"[{host_name}] 网络清理结果: {r}")
                        networks_deleted = len(r.get("NetworksDeleted") or [])
                    except Exception as e:
                        log(f"[{host_name}] 清理网络时出错: {e}")

                if config.get("prune_volumes"):
                    try:
                        log(f"[{host_name}] 清理所有未使用的卷（包括命名卷）…")
                        r = client.volumes.prune(filters={"all": True})
                        log(f"[{host_name}] 卷清理结果: {r}")
                        volumes_deleted_list = r.get("VolumesDeleted") or []
                        volumes_deleted = len(volumes_deleted_list) if volumes_deleted_list else 0
                        space_reclaimed += int(r.get("SpaceReclaimed") or 0)
                    except Exception as e:
                        log(f"[{host_name}] 清理卷时出错: {e}")

                if config.get("prune_build_cache"):
                    try:
                        log(f"[{host_name}] 清理构建缓存…")
                        r = client.api.prune_builds()
                        log(f"[{host_name}] 构建缓存清理结果: {r}")
                        cache_ids_deleted = r.get("CachesDeleted") or []
                        build_cache_deleted = len(cache_ids_deleted) if cache_ids_deleted else 0
                        space_reclaimed += int(r.get("SpaceReclaimed") or 0)
                    except Exception as e:
                        log(f"[{host_name}] 清理构建缓存时出错: {e}")

                log(f"[{host_name}] 清理完成: 容器={containers_deleted}, 镜像={images_deleted}, 网络={networks_deleted}, 卷={volumes_deleted}, 构建缓存={build_cache_deleted}, 空间={human_bytes(space_reclaimed)}")
                
                total_containers_deleted += containers_deleted
                total_images_deleted += images_deleted
                total_networks_deleted += networks_deleted
                total_volumes_deleted += volumes_deleted
                total_build_cache_deleted += build_cache_deleted
                total_space_reclaimed += space_reclaimed
                
                host_results.append({
                    "name": host_name,
                    "url": host_url,
                    "success": True,
                    "containers": containers_deleted,
                    "images": images_deleted,
                    "networks": networks_deleted,
                    "volumes": volumes_deleted,
                    "build_cache": build_cache_deleted,
                    "space": space_reclaimed,
                })
                
            except Exception as e:
                log(f"[{host_name}] 清理过程中出现意外错误: {e}")
                host_results.append({
                    "name": host_name,
                    "url": host_url,
                    "success": False,
                    "error": str(e),
                    "containers": 0,
                    "images": 0,
                    "networks": 0,
                    "volumes": 0,
                    "build_cache": 0,
                    "space": 0,
                })
            finally:
                if client is not None:
                    try:
                        client.close()
                    except Exception:
                        pass

        log("所有主机的清理任务已完成。")

        anything_deleted = any([
            total_containers_deleted, total_images_deleted, total_networks_deleted,
            total_volumes_deleted, total_build_cache_deleted, total_space_reclaimed > 0
        ])

        update_stats(
            containers=total_containers_deleted,
            images=total_images_deleted,
            networks=total_networks_deleted,
            volumes=total_volumes_deleted,
            build_cache=total_build_cache_deleted,
            space=total_space_reclaimed
        )

        if not anything_deleted and config.get("notifications", {}).get("only_on_changes", True):
            log("未清理任何资源; 跳过通知。")
            return True

        summary_lines = [
            f"📅 {describe_schedule()}",
            "",
        ]
        
        if len(all_hosts) > 1:
            summary_lines.append("📊 按主机统计结果:")
        
        for result in host_results:
            if result.get("success"):
                has_deletions = any([result.get('containers'), result.get('images'), result.get('networks'), result.get('volumes'), result.get('build_cache')])
                
                if has_deletions:
                    summary_lines.append(f"• {result['name']}")
                    if result.get('containers'):
                        summary_lines.append(f"  - 🗑️ {result['containers']} 个容器")
                    if result.get('images'):
                        summary_lines.append(f"  - 💿 {result['images']} 个镜像")
                    if result.get('networks'):
                        summary_lines.append(f"  - 🌐 {result['networks']} 个网络")
                    if result.get('volumes'):
                        summary_lines.append(f"  - 📦 {result['volumes']} 个卷")
                    if result.get('build_cache'):
                        summary_lines.append(f"  - 🏗️ {result['build_cache']} 个构建缓存")
                    if result['space']:
                        summary_lines.append(f"  - 💾 回收空间 {human_bytes(result['space'])}")
                else:
                    summary_lines.append(f"• {result['name']}: ✅ 无资源需要清理")
            else:
                summary_lines.append(f"• {result['name']}: ❌ {result.get('error', '未知错误')}")
        
        if len(all_hosts) > 1:
            summary_lines.append("")
        
        if len(all_hosts) > 1:
            summary_lines.append("📈 所有主机总计:")
        if anything_deleted:
            if total_containers_deleted:
                summary_lines.append(f"  - 🗑️ 容器: {total_containers_deleted}")
            if total_images_deleted:
                summary_lines.append(f"  - 💿 镜像: {total_images_deleted}")
            if total_networks_deleted:
                summary_lines.append(f"  - 🌐 网络: {total_networks_deleted}")
            if total_volumes_deleted:
                summary_lines.append(f"  - 📦 卷: {total_volumes_deleted}")
            if total_build_cache_deleted:
                summary_lines.append(f"  - 🏗️ 构建缓存: {total_build_cache_deleted}")
            if total_space_reclaimed:
                summary_lines.append(f"  - 💾 回收空间: {human_bytes(total_space_reclaimed)}")
        else:
            summary_lines.append("✅ 本次运行无资源需要清理")

        message = "\n".join(summary_lines)
        notif_priority = config.get("notifications", {}).get("priority", "medium")
        send_notification("PruneMate 清理完成", message, priority=notif_priority)
        
        return True
    
    finally:
        if acquired:
            try:
                lock.release()
            except Exception:
                pass


def compute_run_key(now: datetime.datetime) -> str:
    """为当前计划任务生成唯一键"""
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
    """检查是否到达计划清理时间并执行清理"""
    load_config(silent=True)
    
    if not config.get("schedule_enabled", True):
        return
    
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
        _, last_day = calendar.monthrange(now.year, now.month)
        actual_dom = min(dom_cfg, last_day)
        if now.day == actual_dom and hour_now == hour_cfg and minute_now == minute_cfg:
            should_run = True

    if not should_run:
        return

    key = compute_run_key(now)
    if last_run_key["value"] == key:
        log(f"计划任务已跳过: 已为键 '{key}' 执行过（内存检查）")
        return
    disk_key = _read_last_run_key()
    if disk_key == key:
        last_run_key["value"] = key
        log(f"计划任务已跳过: 已为键 '{key}' 执行过（磁盘检查）")
        return

    log(f"到达计划时间 ({freq}) 在 {hour_now:02d}:{minute_now:02d}，执行清理。")
    last_run_key["value"] = key
    _write_last_run_key(key)
    ran = run_prune_job(origin="scheduled", wait=False)
    if not ran:
        pass


def heartbeat():
    """心跳函数，每分钟检查一次计划任务"""
    log("心跳: 调度器运行正常。")
    check_and_run_scheduled_job()


# ---- 认证逻辑 ----
def is_auth_enabled():
    """检查是否启用了身份验证"""
    return bool(os.environ.get("PRUNEMATE_AUTH_PASSWORD_HASH"))


def check_auth(username, password):
    """验证用户名和密码"""
    expected_user = os.environ.get("PRUNEMATE_AUTH_USER", "admin")
    password_hash = os.environ.get("PRUNEMATE_AUTH_PASSWORD_HASH")

    if not password_hash:
        return False

    if username != expected_user:
        return False

    try:
        password_hash = base64.b64decode(password_hash).decode("utf-8")
    except Exception:
        pass
    
    try:
        return check_password_hash(password_hash, password)
    except Exception:
        return False


def request_wants_json():
    """检查客户端是否需要JSON响应"""
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


@app.before_request
def require_auth():
    """请求前检查身份验证"""
    if not is_auth_enabled():
        return

    if request.endpoint in ('static', 'login', 'logout', 'stats', 'api_stats'):
        return

    if session.get('logged_in'):
        return

    auth = request.authorization
    if auth:
        if check_auth(auth.username, auth.password):
            return
    
    ua = request.user_agent.string.lower()
    is_browser = any(x in ua for x in ['mozilla', 'chrome', 'safari', 'edge']) and 'curl' not in ua and 'python' not in ua
    
    if not is_browser or request_wants_json() or request.path.startswith('/api/'):
        return Response(
            '无法验证您的访问权限。\n'
            '您需要使用正确的凭据登录。', 401,
            {'WWW-Authenticate': 'Basic realm="PruneMate 登录"'}
        )
    
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页面处理"""
    if session.get('logged_in'):
        return redirect(url_for('index'))

    if not is_auth_enabled():
        return redirect(url_for("index"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if check_auth(username, password):
            session['logged_in'] = True
            session['user'] = username
            
            next_url = request.args.get('next')
            if not next_url or next_url.startswith('//') or ':' in next_url:
                next_url = url_for('index')
            
            return redirect(next_url)
        else:
            flash("无效的凭据", "error")
            
    return render_template("login.html")


@app.route("/logout")
def logout():
    """登出处理"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    """主页配置页面"""
    load_config(silent=True)
    return render_template("index.html", config=config, timezone=tz_name, config_path=CONFIG_PATH, use_24h=use_24h_format)


@app.route("/update", methods=["POST"])
def update():
    """处理配置更新"""
    load_config(silent=True)
    old_config = json.loads(json.dumps(config))

    frequency = request.form.get("frequency", "daily")
    
    if use_24h_format:
        time_value = request.form.get("time", "03:00")
    else:
        try:
            hour_12 = int(request.form.get("time_hour", "3"))
            minute = int(request.form.get("time_minute", "0"))
            period = request.form.get("time_period", "AM")
            
            hour_12 = max(1, min(12, hour_12))
            minute = max(0, min(59, minute))
            
            if period == "AM":
                hour_24 = 0 if hour_12 == 12 else hour_12
            else:
                hour_24 = 12 if hour_12 == 12 else hour_12 + 12
            
            time_value = f"{hour_24:02d}:{minute:02d}"
        except Exception:
            time_value = "03:00"
    
    day_of_week = request.form.get("day_of_week", "mon")
    raw_dom = request.form.get("day_of_month", "1")
    try:
        day_of_month = int(raw_dom)
    except Exception:
        day_of_month = 1
    day_of_month = max(1, min(31, day_of_month))

    schedule_enabled = "schedule_enabled" in request.form
    prune_containers = "prune_containers" in request.form
    prune_images = "prune_images" in request.form
    prune_networks = "prune_networks" in request.form
    prune_volumes = "prune_volumes" in request.form
    prune_build_cache = "prune_build_cache" in request.form

    provider = request.form.get("notifications_provider", "gotify")
    gotify_enabled = "gotify_enabled" in request.form
    gotify_url = (request.form.get("gotify_url") or "").strip()
    gotify_token = (request.form.get("gotify_token") or "").strip()
    ntfy_enabled = "ntfy_enabled" in request.form
    ntfy_url = (request.form.get("ntfy_url") or "").strip()
    ntfy_topic = (request.form.get("ntfy_topic") or "").strip()
    ntfy_token = (request.form.get("ntfy_token") or "").strip()
    discord_enabled = "discord_enabled" in request.form
    discord_webhook_url = (request.form.get("discord_webhook_url") or "").strip()
    telegram_enabled = "telegram_enabled" in request.form
    telegram_bot_token = (request.form.get("telegram_bot_token") or "").strip()
    telegram_chat_id = (request.form.get("telegram_chat_id") or "").strip()
    notification_priority = request.form.get("notification_priority", "medium").strip().lower()
    if notification_priority not in ["low", "medium", "high"]:
        notification_priority = "medium"
    only_on_changes = "notifications_only_on_changes" in request.form

    if provider == "gotify" and not gotify_enabled and gotify_url and gotify_token:
        gotify_enabled = True
    if provider == "ntfy" and not ntfy_enabled and ntfy_url and ntfy_topic:
        ntfy_enabled = True
    if provider == "discord" and not discord_enabled and discord_webhook_url:
        discord_enabled = True
    if provider == "telegram" and not telegram_enabled and telegram_bot_token and telegram_chat_id:
        telegram_enabled = True

    time_value = validate_time(time_value)

    new_values = {
        "schedule_enabled": schedule_enabled,
        "frequency": frequency,
        "time": time_value,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "prune_containers": prune_containers,
        "prune_images": prune_images,
        "prune_networks": prune_networks,
        "prune_volumes": prune_volumes,
        "prune_build_cache": prune_build_cache,
        "notifications": {
            "provider": provider,
            "gotify": {"enabled": gotify_enabled, "url": gotify_url, "token": gotify_token},
            "ntfy": {"enabled": ntfy_enabled, "url": ntfy_url, "topic": ntfy_topic, "token": ntfy_token},
            "discord": {"enabled": discord_enabled, "webhook_url": discord_webhook_url},
            "telegram": {"enabled": telegram_enabled, "bot_token": telegram_bot_token, "chat_id": telegram_chat_id},
            "priority": notification_priority,
            "only_on_changes": only_on_changes,
        },
    }

    schedule_keys = [
        "schedule_enabled","frequency","time","day_of_week","day_of_month",
        "prune_containers","prune_images","prune_networks","prune_volumes","prune_build_cache"
    ]
    schedule_changed = any(new_values[k] != old_config.get(k) for k in schedule_keys)
    config.update(new_values)
    if schedule_changed:
        _clear_last_run_key()

    save_config()
    flash("配置已更新。", "success")
    return redirect(url_for("index"))


@app.route("/run-now", methods=["POST"])
def run_now():
    """立即执行清理"""
    load_config(silent=True)
    log("手动清理触发已收到。")
    ran = run_prune_job(origin="manual", wait=True)
    flash("手动清理已执行。" if ran else "清理任务跳过（忙或超时）。", "info")
    return redirect(url_for("index"))


@app.route("/preview-prune", methods=["POST"])
def preview_prune():
    """获取清理预览"""
    load_config(silent=True)
    
    try:
        data = request.get_json() or {}
        if any(k in data for k in ["prune_containers", "prune_images", "prune_networks", "prune_volumes", "prune_build_cache"]):
            config["prune_containers"] = data.get("prune_containers", False)
            config["prune_images"] = data.get("prune_images", False)
            config["prune_networks"] = data.get("prune_networks", False)
            config["prune_volumes"] = data.get("prune_volumes", False)
            config["prune_build_cache"] = data.get("prune_build_cache", False)
            save_config()
            log("清理预览请求已收到并保存更新后的配置。")
    except Exception as e:
        log(f"解析清理预览请求体时出错: {e}")
    
    log("清理预览请求已收到。")
    preview = get_prune_preview()
    return jsonify(preview)


@app.route("/run-confirmed", methods=["POST"])
def run_confirmed():
    """确认后执行清理"""
    load_config(silent=True)
    
    try:
        data = request.get_json() or {}
        if any(k in data for k in ["prune_containers", "prune_images", "prune_networks", "prune_volumes", "prune_build_cache"]):
            config["prune_containers"] = data.get("prune_containers", False)
            config["prune_images"] = data.get("prune_images", False)
            config["prune_networks"] = data.get("prune_networks", False)
            config["prune_volumes"] = data.get("prune_volumes", False)
            config["prune_build_cache"] = data.get("prune_build_cache", False)
            save_config()
            log("确认清理触发已收到并保存更新后的配置。")
    except Exception as e:
        log(f"解析确认清理请求体时出错: {e}")
    
    log("确认手动清理触发已收到。")
    ran = run_prune_job(origin="manual", wait=True)
    return jsonify({
        "success": ran,
        "message": "清理任务已成功执行。" if ran else "清理任务跳过（忙或超时）。"
    })


@app.route("/test-notification", methods=["POST"])
def test_notification():
    """发送测试通知"""
    load_config(silent=True)
    old_config = json.loads(json.dumps(config))

    frequency = request.form.get("frequency", "daily")
    
    if use_24h_format:
        time_value = request.form.get("time", "03:00")
    else:
        try:
            hour_12 = int(request.form.get("time_hour", "3"))
            minute = int(request.form.get("time_minute", "0"))
            period = request.form.get("time_period", "AM")
            
            hour_12 = max(1, min(12, hour_12))
            minute = max(0, min(59, minute))
            
            if period == "AM":
                hour_24 = 0 if hour_12 == 12 else hour_12
            else:
                hour_24 = 12 if hour_12 == 12 else hour_12 + 12
            
            time_value = f"{hour_24:02d}:{minute:02d}"
        except Exception:
            time_value = "03:00"
    
    day_of_week = request.form.get("day_of_week", "mon")
    raw_dom = request.form.get("day_of_month", "1")
    try:
        day_of_month = int(raw_dom)
    except Exception:
        day_of_month = 1
    day_of_month = max(1, min(31, day_of_month))

    prune_containers = "prune_containers" in request.form
    prune_images = "prune_images" in request.form
    prune_networks = "prune_networks" in request.form
    prune_volumes = "prune_volumes" in request.form
    prune_build_cache = "prune_build_cache" in request.form

    provider = request.form.get("notifications_provider", "gotify")
    gotify_enabled = "gotify_enabled" in request.form
    gotify_url = (request.form.get("gotify_url") or "").strip()
    gotify_token = (request.form.get("gotify_token") or "").strip()
    ntfy_enabled = "ntfy_enabled" in request.form
    ntfy_url = (request.form.get("ntfy_url") or "").strip()
    ntfy_topic = (request.form.get("ntfy_topic") or "").strip()
    ntfy_token = (request.form.get("ntfy_token") or "").strip()
    discord_enabled = "discord_enabled" in request.form
    discord_webhook_url = (request.form.get("discord_webhook_url") or "").strip()
    telegram_enabled = "telegram_enabled" in request.form
    telegram_bot_token = (request.form.get("telegram_bot_token") or "").strip()
    telegram_chat_id = (request.form.get("telegram_chat_id") or "").strip()
    notification_priority = request.form.get("notification_priority", "medium").strip().lower()
    if notification_priority not in ["low", "medium", "high"]:
        notification_priority = "medium"
    only_on_changes = "notifications_only_on_changes" in request.form

    if provider == "gotify" and not gotify_enabled and gotify_url and gotify_token:
        gotify_enabled = True
    if provider == "ntfy" and not ntfy_enabled and ntfy_url and ntfy_topic:
        ntfy_enabled = True
    if provider == "discord" and not discord_enabled and discord_webhook_url:
        discord_enabled = True
    if provider == "telegram" and not telegram_enabled and telegram_bot_token and telegram_chat_id:
        telegram_enabled = True

    time_value = validate_time(time_value)

    new_values = {
        "frequency": frequency,
        "time": time_value,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "prune_containers": prune_containers,
        "prune_images": prune_images,
        "prune_networks": prune_networks,
        "prune_volumes": prune_volumes,
        "prune_build_cache": prune_build_cache,
        "notifications": {
            "provider": provider,
            "gotify": {"enabled": gotify_enabled, "url": gotify_url, "token": gotify_token},
            "ntfy": {"enabled": ntfy_enabled, "url": ntfy_url, "topic": ntfy_topic, "token": ntfy_token},
            "discord": {"enabled": discord_enabled, "webhook_url": discord_webhook_url},
            "telegram": {"enabled": telegram_enabled, "bot_token": telegram_bot_token, "chat_id": telegram_chat_id},
            "priority": notification_priority,
            "only_on_changes": only_on_changes,
        },
    }

    schedule_keys = [
        "frequency","time","day_of_week","day_of_month",
        "prune_containers","prune_images","prune_networks","prune_volumes","prune_build_cache"
    ]
    schedule_changed = any(new_values[k] != old_config.get(k) for k in schedule_keys)
    config.update(new_values)
    if schedule_changed:
        _clear_last_run_key()

    save_config()
    
    log("从UI请求通知测试。")
    test_priority = config.get("notifications", {}).get("priority", "medium")
    ok = send_notification(
        "PruneMate 测试通知",
        "这是来自 PruneMate 的测试消息。\n\n如果您看到此消息，说明您的通知提供商配置工作正常。",
        priority=test_priority,
    )
    flash("配置已保存。 " + ("测试通知已发送。" if ok else "测试通知发送失败（请检查设置和日志）。"), "info")
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    """返回历史统计数据"""
    return jsonify(load_stats())


@app.route("/api/stats")
def api_stats():
    """返回格式化的统计数据"""
    stats = load_stats()
    
    last_run_text = "从未"
    last_run_timestamp = None
    if stats.get("last_run"):
        try:
            last_run_dt = datetime.datetime.fromisoformat(stats["last_run"])
            now = datetime.datetime.now(app_timezone)
            
            if last_run_dt.tzinfo is None:
                last_run_dt = last_run_dt.replace(tzinfo=app_timezone)
            
            delta = now - last_run_dt
            
            if delta.days > 0:
                last_run_text = f"{delta.days}天前"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                last_run_text = f"{hours}小时前"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                last_run_text = f"{minutes}分钟前"
            else:
                last_run_text = "刚刚"
            
            last_run_timestamp = int(last_run_dt.timestamp())
        except (ValueError, TypeError, OSError) as e:
            log(f"解析上次运行时间戳时出错: {e}")
            last_run_text = "未知"
        except Exception as e:
            log(f"/api/stats 时间戳计算中出现意外错误: {e}")
            last_run_text = "未知"
    
    return jsonify({
        "pruneRuns": stats.get("prune_runs", 0),
        "containersDeleted": stats.get("containers_deleted", 0),
        "imagesDeleted": stats.get("images_deleted", 0),
        "networksDeleted": stats.get("networks_deleted", 0),
        "volumesDeleted": stats.get("volumes_deleted", 0),
        "buildCacheDeleted": stats.get("build_cache_deleted", 0),
        "spaceReclaimed": stats.get("total_space_reclaimed", 0),
        "spaceReclaimedHuman": human_bytes(stats.get("total_space_reclaimed", 0)),
        "firstRun": stats.get("first_run"),
        "lastRun": stats.get("last_run"),
        "lastRunText": last_run_text,
        "lastRunTimestamp": last_run_timestamp
    })


@app.route("/hosts")
def list_hosts():
    """返回Docker主机列表"""
    load_config(silent=True)
    external_hosts = config.get("docker_hosts", [])
    
    all_hosts = [
        {"name": "本地", "url": "unix:///var/run/docker.sock", "enabled": True}
    ] + external_hosts
    
    return jsonify({"hosts": all_hosts})


@app.route("/hosts/add", methods=["POST"])
def add_host():
    """添加新的Docker主机"""
    load_config(silent=True)
    
    name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    enabled = "enabled" in request.form
    
    if not name or not url:
        flash("主机名称和URL是必填项。", "warn")
        return redirect(url_for("index"))
    
    valid_protocols = ["tcp://", "http://", "https://"]
    if not any(url.startswith(proto) for proto in valid_protocols):
        flash("URL必须以 tcp://, http://, 或 https:// 开头", "warn")
        return redirect(url_for("index"))
    
    new_host = {
        "name": name,
        "url": url,
        "enabled": enabled
    }
    
    if "docker_hosts" not in config:
        config["docker_hosts"] = []
    
    config["docker_hosts"].append(new_host)
    save_config()
    
    flash(f"Docker主机 '{name}' 添加成功。", "info")
    return redirect(url_for("index"))


@app.route("/hosts/<int:index>/update", methods=["POST"])
def update_host(index):
    """更新现有的Docker主机"""
    load_config(silent=True)
    
    hosts = config.get("docker_hosts", [])
    if index < 0 or index >= len(hosts):
        flash("无效的主机索引。", "warn")
        return redirect(url_for("index"))
    
    name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    enabled = "enabled" in request.form
    
    if not name or not url:
        flash("主机名称和URL是必填项。", "warn")
        return redirect(url_for("index"))
    
    valid_protocols = ["tcp://", "http://", "https://"]
    if not any(url.startswith(proto) for proto in valid_protocols):
        flash("URL必须以 tcp://, http://, 或 https:// 开头", "warn")
        return redirect(url_for("index"))
    
    hosts[index] = {
        "name": name,
        "url": url,
        "enabled": enabled
    }
    
    config["docker_hosts"] = hosts
    save_config()
    
    flash(f"Docker主机 '{name}' 更新成功。", "info")
    return redirect(url_for("index"))


@app.route("/hosts/<int:index>/delete", methods=["POST"])
def delete_host(index):
    """删除Docker主机"""
    load_config(silent=True)
    
    hosts = config.get("docker_hosts", [])
    if index < 0 or index >= len(hosts):
        flash("无效的主机索引。", "warn")
        return redirect(url_for("index"))
    
    deleted_name = hosts[index].get("name", "未知")
    del hosts[index]
    
    config["docker_hosts"] = hosts
    save_config()
    
    flash(f"Docker主机 '{deleted_name}' 删除成功。", "info")
    return redirect(url_for("index"))


@app.route("/hosts/<int:index>/toggle", methods=["POST"])
def toggle_host(index):
    """切换Docker主机的启用/禁用状态"""
    load_config(silent=True)
    
    hosts = config.get("docker_hosts", [])
    if index < 0 or index >= len(hosts):
        return jsonify({"success": False, "error": "无效的主机索引"}), 400
    
    hosts[index]["enabled"] = not hosts[index].get("enabled", True)
    config["docker_hosts"] = hosts
    save_config()
    
    status = "已启用" if hosts[index]["enabled"] else "已禁用"
    return jsonify({"success": True, "enabled": hosts[index]["enabled"], "message": f"主机已{status}"})


class StandaloneApplication(BaseApplication):
    """自定义Gunicorn应用"""
    
    def __init__(self, app, options=None):
        """初始化Gunicorn应用"""
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """加载Gunicorn配置"""
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """返回Flask应用实例"""
        return self.application


if __name__ == "__main__":
    load_config()
    scheduler.add_job(heartbeat, CronTrigger(second=0), id="heartbeat", max_instances=1, coalesce=True)
    log("调度器心跳任务已启动（每分钟在:00 执行）。")
    
    options = {
        "bind": "0.0.0.0:8080",
        "workers": 1,
        "threads": 2,
        "timeout": 120,
        "accesslog": None,
        "errorlog": "-",
        "loglevel": "info",
    }
    StandaloneApplication(app, options).run()