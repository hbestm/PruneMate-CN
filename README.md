# PruneMate

<p align="center">
  <img width="400" height="400" alt="prunemate-logo" src="https://github.com/user-attachments/assets/0785ea56-88f6-4926-9ae1-de736840c378" />
</p>

<h1 align="center">PruneMate</h1>
<p align="center"><em>Docker image & resource cleanup helper, on a schedule!</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.7-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/python-3.12-yellow?style=for-the-badge&logo=python&logoColor=ffffff"/>
  <img src="https://img.shields.io/badge/docker-compose-0db7ed?style=for-the-badge&logo=docker&logoColor=ffffff"/>
  <img src="https://img.shields.io/badge/license-AGPLv3-orange?style=for-the-badge"/>
  <a href="https://hub.docker.com/r/anoniemerd/prunemate">
    <img src="https://img.shields.io/docker/pulls/anoniemerd/prunemate?style=for-the-badge&logo=docker&logoColor=ffffff&label=docker%20pulls"/>
  </a>
</p>

A sleek, lightweight web interface to **automatically clean up Docker resources** on a schedule. Built with Python (Flask) · Docker SDK · APScheduler · Gunicorn

**Keep your Docker host tidy with scheduled cleanup of unused images, containers, networks, and volumes.**

> ⚠️ **DISCLAIMER**: PruneMate deletes Docker resources. Ensure you understand what will be pruned before enabling automated schedules. The author is not responsible for any data loss or system issues. **Use at your own risk.**

---

## ✨ Features

- 🕐 **Flexible scheduling** - Daily, Weekly, or Monthly cleanup runs
- 🌍 **Timezone aware** - Configure your local timezone
- 🕒 **12/24-hour time format** - Choose your preferred time display
- 🐳 **Multi-host support** - Manage multiple Docker hosts from one interface (requires docker-socket-proxy on remote hosts)
- 🧹 **Selective cleanup** - Choose what to prune: containers, images, networks, volumes
- 📊 **All-Time Statistics** - Track cumulative space reclaimed and resources deleted across all runs
- 🔔 **Smart notifications** - Gotify or ntfy.sh support with Bearer token & Basic Auth, optional change-only alerts
- 🎨 **Modern UI** - Dark theme with smooth animations and responsive design
- 🔒 **Safe & controlled** - Manual trigger option and detailed logging
- 📈 **Detailed reports** - See exactly what was cleaned and how much space was reclaimed

---

## 📷 Screenshots

### Main Dashboard
The overall look and feel of the PruneMate dashboard

<p align="center">
  <img width="400" height="800" src="https://github.com/user-attachments/assets/4e4eb62b-f812-4ec3-8fed-02aedca174db" />

</p>

### Main Dashboard - All-Time Statistics
Track cumulative prune statistics showing total space reclaimed, resources deleted, and run history.

<p align="center">
  <img width="400" height="400" alt="prunemate-statistics" src="https://github.com/user-attachments/assets/206d9787-58d8-4756-ab7f-d5b9dccfad5d" /> 
</p>

### Schedule Configuration
Configure when and how often PruneMate should clean up your Docker resources.

<p align="center">
  <img width="400" height="400" alt="prunemate-schedule" src="https://github.com/user-attachments/assets/3a822897-5ede-4476-b570-f4d8adf37867" /> 
</p>

### Cleanup Options
Select which Docker resources to clean up and configure advanced options.

<p align="center">
  <img width="400" height="400" alt="prunemate-cleanup" src="https://github.com/user-attachments/assets/70ae1e8f-49a1-4c89-ac46-685d804ee3db" />
</p>

### External Docker hosts
Add external Docker hosts via [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)

<p align="center">
  <img width="400" height="400" alt="prunemate-cleanup" src="https://github.com/user-attachments/assets/28abdbe4-bd9e-4272-a6fc-24a4a8dc83bb" />
</p>

### Notification Settings
Set up notifications via Gotify or ntfy.sh to stay informed about cleanup results.

<p align="center">
  <img width="400" height="400" alt="prunemate-notifications" src="https://github.com/user-attachments/assets/73a06c4d-fffa-40eb-a010-239d7d364004" /> 
</p>

### Cleanup Results
Get detailed statistics notifications about what was cleaned and how much space was reclaimed.

Gotify :
<p align="center">
  <img width="400" height="400" alt="prunemate-results" src="https://github.com/user-attachments/assets/757ce7d2-7e7e-409b-ae01-745262a067c7" />

</p>

ntfy :
<p align="center">
  <img width="400" height="400" alt="prunemate-results" src="https://github.com/user-attachments/assets/fd214db5-34ef-4e3b-8c73-b78262964739" />

</p>


---

## 🚀 Quick Start with Docker Compose

### Prerequisites

- Docker and Docker Compose installed
- Access to Docker socket (`/var/run/docker.sock`)

### Installation

1. **Create a `docker-compose.yaml` file:**

```yaml
services:
  prunemate:
    image: anoniemerd/prunemate:latest
    container_name: prunemate
    ports:
      - "7676:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs:/var/log
      - ./config:/config
    environment:
      - PRUNEMATE_TZ=Europe/Amsterdam # Change this to your desired timezone
      - PRUNEMATE_TIME_24H=true #false for 12-Hour format (AM/PM)
    restart: unless-stopped
```

**For ARM64 systems (Apple Silicon, ARM servers, Raspberry Pi):**

If you get "no matching manifest for linux/arm64" error, clone the repository and build locally:

```bash
# Clone the repository
git clone https://github.com/anoniemerd/PruneMate.git
cd PruneMate
```

Then use this docker-compose.yaml:

```yaml
services:
  prunemate:
    build: .  # Build locally instead of using pre-built image
    container_name: prunemate
    ports:
      - "7676:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs:/var/log
      - ./config:/config
    environment:
      - PRUNEMATE_TZ=Europe/Amsterdam # Change this to your desired timezone
      - PRUNEMATE_TIME_24H=true #false for 12-Hour format (AM/PM)
    restart: unless-stopped
```

2. **Start PruneMate:**

```bash
docker-compose up -d
```

3. **Access the web UI of PruneMate:**

Open your browser and navigate to:

```
http://<your-server-ip>:7676/
```

---

## 🚀 Quick Start with Docker Run

**Using Docker CLI:**

```bash
docker run -d \
  --name prunemate \
  -p 7676:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/logs:/var/log \
  -v $(pwd)/config:/config \
  -e PRUNEMATE_TZ=Europe/Amsterdam \
  -e PRUNEMATE_TIME_24H=true \
  --restart unless-stopped \
  anoniemerd/prunemate:latest
```

**Access the web UI:**

```
http://<your-server-ip>:7676/
```



**Volume explanations:**
- `/var/run/docker.sock` - Required for Docker API access
- `./logs` - Stores application logs (rotating, 5MB max per file)
- `./config` - Stores configuration and state files

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRUNEMATE_TZ` | `UTC` | Timezone for scheduling (e.g., `Europe/Amsterdam`, `America/New_York`) |
| `PRUNEMATE_TIME_24H` | `true` | Time format: `true` for 24-hour, `false` for 12-hour (AM/PM) |
| `PRUNEMATE_CONFIG` | `/config/config.json` | Path to configuration file |

### Web Interface Settings

Access the web interface at `http://localhost:7676/` (or your server IP) to configure:

**Schedule Settings:**
- **Frequency:** Daily, Weekly, or Monthly
- **Time:** When to run the cleanup (supports both 12h and 24h format)
- **Day:** Day of week (for weekly) or day of month (for monthly)

**Cleanup Options:**
- ☑️ All unused containers
- ☑️ All unused images  
- ☑️ All unused networks
- ☑️ All unused volumes

**Notification Settings:**
- **Provider:** Gotify or ntfy.sh
- **URL:** Your notification server URL
- **Token/Topic:** Authentication token (Gotify) or topic name (ntfy)
- **Only notify on changes:** Only send notifications when something was actually cleaned

---

## 🧠 How it works

1. **Scheduler runs** every minute checking if it's time to execute
2. **Loads latest config** from persistent storage
3. **Executes Docker prune** commands for selected resource types
4. **Collects statistics** on what was removed and space reclaimed
5. **Updates all-time statistics** with cumulative data (space, counts, timestamps)
6. **Sends notification** (if configured and enabled)
7. **Logs everything** with timezone-aware timestamps

### Architecture Flowchart

```mermaid
flowchart TD
    Start([Start PruneMate]) --> WebUI[Web Interface<br/>Flask + Gunicorn<br/>Port 8080]
    Start --> Scheduler[APScheduler<br/>Checks every minute]
    
    WebUI --> |User configures| ConfigFile[(config.json<br/>/config/)]
    
    Scheduler --> CheckTime{Time to<br/>run prune?}
    CheckTime --> |No| Wait[Wait 1 minute]
    Wait --> Scheduler
    
    CheckTime --> |Yes| LoadConfig[Load config.json]
    LoadConfig --> CheckLock{Lock file<br/>exists?}
    CheckLock --> |Yes| Skip[Skip run<br/>Already running]
    Skip --> Scheduler
    
    CheckLock --> |No| CreateLock[Create prunemate.lock]
    CreateLock --> ConnectDocker[Connect to Docker<br/>via Unix socket]
    
    ConnectDocker --> MultiHost{Multiple<br/>hosts enabled?}
    MultiHost --> |Yes| ConnectRemote[Connect to remote hosts<br/>via docker-socket-proxy]
    MultiHost --> |No| LocalOnly[Local host only]
    
    ConnectRemote --> PruneLoop[Execute prune operations<br/>per host]
    LocalOnly --> PruneLoop
    
    PruneLoop --> CheckContainers{Prune<br/>containers?}
    CheckContainers --> |Yes| PruneContainers[docker container prune]
    CheckContainers --> |No| CheckImages{Prune<br/>images?}
    
    PruneContainers --> CheckImages
    CheckImages --> |Yes| PruneImages[docker image prune -a]
    CheckImages --> |No| CheckNetworks{Prune<br/>networks?}
    
    PruneImages --> CheckNetworks
    CheckNetworks --> |Yes| PruneNetworks[docker network prune]
    CheckNetworks --> |No| CheckVolumes{Prune<br/>volumes?}
    
    PruneNetworks --> CheckVolumes
    CheckVolumes --> |Yes| PruneVolumes[docker volume prune]
    CheckVolumes --> |No| CollectStats[Collect statistics<br/>Space reclaimed, items deleted]
    
    PruneVolumes --> CollectStats
    
    CollectStats --> UpdateStats[Update stats.json<br/>Cumulative totals]
    UpdateStats --> CheckNotif{Notifications<br/>enabled?}
    
    CheckNotif --> |No| LogResults[Write to prunemate.log]
    CheckNotif --> |Yes| CheckChanges{Only notify<br/>on changes?}
    
    CheckChanges --> |Yes & No changes| LogResults
    CheckChanges --> |No or Has changes| SendNotif[Send notification<br/>Gotify or ntfy]
    
    SendNotif --> LogResults
    LogResults --> RemoveLock[Remove prunemate.lock]
    RemoveLock --> UpdateUI[Update web UI<br/>with latest stats]
    UpdateUI --> Scheduler
    
    WebUI -.-> |Manual trigger| CreateLock
    
    style Start fill:#4a90e2
    style WebUI fill:#50c878
    style Scheduler fill:#9b59b6
    style ConfigFile fill:#f39c12
    style PruneLoop fill:#e74c3c
    style UpdateStats fill:#16a085
    style SendNotif fill:#3498db
```

### File Structure

```
/config/
├── config.json          # Your configuration (persistent)
├── stats.json           # All-time statistics (cumulative data)
├── prunemate.lock       # Prevents concurrent runs
└── last_run_key         # Tracks last successful run

/var/log/
└── prunemate.log        # Application logs (rotating, 5MB max)
```

### All-Time Statistics

PruneMate tracks cumulative statistics across all prune runs:

**Metrics tracked:**
- 💾 **Total Space Reclaimed** - Cumulative disk space freed (displayed in MB/GB/TB)
- 📦 **Containers Deleted** - Total count of unused containers removed
- 🖼️ **Images Deleted** - Total count of unused images removed
- 🔗 **Networks Deleted** - Total count of unused networks removed
- 💿 **Volumes Deleted** - Total count of unused volumes removed
- 🔄 **Total Prune Runs** - Number of times prune has executed
- 📅 **First Run** - Timestamp of the very first prune execution
- 🕐 **Last Run** - Timestamp of the most recent prune execution

**Technical details:**
- Statistics persist in `/config/stats.json` using atomic writes with file locking
- Updates occur after every prune run, regardless of whether resources were deleted
- Timestamps are timezone-aware and respect `PRUNEMATE_TZ` setting
- Date/time display in UI follows configured 12h/24h format
- Statistics survive container restarts and updates
- Auto-refresh after manual prune runs via web interface

---

## 🔔 Notification Setup

### Gotify

[Gotify](https://gotify.net/) is a self-hosted notification service.

**Setup steps:**
1. Install and run Gotify server
2. Create a new application in Gotify
3. Copy the application token
4. Configure in PruneMate:
   - **Provider:** Gotify
   - **URL:** `https://your-gotify-server.com`
   - **Token:** Your application token

### ntfy.sh

[ntfy.sh](https://ntfy.sh/) is a simple pub-sub notification service (self-hosted or public).

**Setup steps:**
1. Choose a unique topic name (e.g., `prunemate-alerts`)
2. Configure in PruneMate:
   - **Provider:** ntfy
   - **URL:** `https://ntfy.sh` (or your self-hosted instance, supports `username:password@host` format)
   - **Topic:** Your chosen topic name
   - **Token:** (Optional) Bearer token for authentication

**Authentication options:**
- **Bearer token:** Recommended for API access tokens (higher priority)
- **URL credentials:** Use `https://username:password@ntfy.example.com` format (RFC 3986 compliant)
- **No authentication:** Works with public topics

**Subscribe to notifications:**
- **Web:** Visit `https://ntfy.sh/your-topic`
- **Mobile:** Install the ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)) and subscribe to your topic
- **Desktop:** Use ntfy desktop app or web browser

---

## 🌐 Multi-Host Setup (Optional)

PruneMate can manage multiple Docker hosts from a single interface. Each prune operation runs across all enabled hosts with aggregated results.

### Security First: Use Docker Socket Proxy

⚠️ **Never expose Docker sockets directly!** Always use [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) to limit API access.

### Quick Setup

**1. Deploy proxy on each remote host:**

```yaml
services:
  dockerproxy:
    image: ghcr.io/tecnativa/docker-socket-proxy:latest
    environment:
      - CONTAINERS=1
      - IMAGES=1
      - NETWORKS=1
      - VOLUMES=1
      - POST=1          # Required for prune operations
    ports:
      - "2375:2375"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
```

**2. Add hosts in PruneMate UI:**
- Navigate to **Docker Hosts** section
- Click **Add New Host**
- Enter name (e.g., "NAS") and URL (e.g., `tcp://192.168.1.50:2375`)
- Toggle hosts on/off as needed

**3. Test connection:**
Click **Run now** and check logs for successful connection to all hosts.


### Troubleshooting

- **Connection refused**: Verify proxy is running (`docker ps`) and port 2375 is accessible
- **Permission denied**: Ensure proxy has `POST=1` environment variable
- **Host skipped**: Check URL format starts with `tcp://`, `http://`, or `https://`

---

## 🧠 Troubleshooting

| Problem | Solution |
|---------|----------|
| ❌ Can't access web interface | • Check if port 7676 is available and not blocked by firewall<br>• Verify container is running: `docker ps`<br>• Check logs: `docker logs prunemate` |
| 🏗️ ARM architecture error | • Error: "no matching manifest for linux/arm64"<br>• **Solution:** Clone the repository and change `image: anoniemerd/prunemate:latest` to `build: .` in docker-compose.yaml<br>• This builds the image locally for your ARM64 system<br>• See Quick Start section for ARM64-specific instructions |
| ⚙️ Container not starting | • View startup errors: `docker logs prunemate`<br>• Verify Docker socket is accessible<br>• Check if port 7676 is already in use |
| 🔒 Permission denied errors | • Ensure `/var/run/docker.sock` exists and is accessible<br>• On Linux, Docker daemon must be running<br>• User running Docker must have proper permissions |
| 🕐 Wrong timezone in logs/schedule | • Set `PRUNEMATE_TZ` environment variable correctly<br>• Restart container after changing: `docker-compose restart`<br>• Verify timezone in logs matches expected |
| 📧 Notifications not working | • Test notification settings in web interface<br>• Verify notification server URL is accessible<br>• Check token/topic is correct<br>• Review logs for error messages |
| 🗂️ Configuration not persisting | • Ensure `./config` volume is mounted correctly<br>• Check file permissions on host `./config` directory<br>• Verify container has write access |
| 🧹 Cleanup not running on schedule | • Check schedule configuration in web interface<br>• Verify timezone is set correctly<br>• Review logs: "Next scheduled run" messages<br>• Ensure container is running continuously |

---

### Logging

**What the logs contain:**
- ✅ Scheduler heartbeats (every minute)
- 📝 Configuration changes
- 🧹 Prune job executions with results
- 📨 Notification delivery status
- ❌ Error messages and warnings

---

## 📜 Release Notes

### Version 1.2.7 (December 2025)
- 🔐 **NEW** ntfy authentication support - Bearer token and Basic Auth (username:password in URL)
  - Priority system: Bearer token → Basic Auth → unauthenticated
  - RFC 3986 compliant URL parsing for embedded credentials
- 🔒 **NEW** Enhanced credential security - Passwords and tokens masked in all log output
- 🎨 **Improved:** Logo enhancement by [@shollyethan](https://github.com/shollyethan) + added to the Self-Hosted Dashboard Icons on https://selfh.st/icons/
- 📏 **Improved:** Logo size increased from 76×76px to 82×82px
- 📱 **Improved:** Better mobile support - Enhanced responsive design for smartphone usage
- 🔔 **Improved:** Notification panel height increased to 900px with enhanced scrolling
- 🔧 **Improved:** Config migration with deep merge strategy prevents data loss during upgrades
- 📊 **Improved:** Stats persistence with forward-compatible field migration and type safety
- 🐛 **Fixed:** Config shallow merge bug causing nested key loss during v1.2.6 → v1.2.7 upgrades
- 🐛 **Fixed:** Legacy notification migration incomplete (ntfy credentials not preserved)
- 🐛 **Fixed:** Stats type safety issues with corrupt JSON files
- 🐛 **Fixed:** Notification panel button visibility on smaller screens

📖 **[View full changelog](CHANGELOG.md)**

---

## 📬 Support

Have questions or need help?

- 🐛 **Bug reports:** [Open an issue on GitHub](https://github.com/anoniemerd/PruneMate/issues)
- 💡 **Feature requests:** [Open an issue on GitHub](https://github.com/anoniemerd/PruneMate/issues)
- 💬 **Questions & Discussion:** [Start a discussion on GitHub](https://github.com/anoniemerd/PruneMate/discussions)
- ⭐ **Like PruneMate?** Give it a star!

---

## 👤 Author & License

**Author:** Anoniemerd  
🐙 GitHub: <https://github.com/anoniemerd>  
📦 Repository: <https://github.com/anoniemerd/PruneMate>

### 📜 License — AGPLv3

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

By using, modifying, or distributing this software, you **must**:

- Keep this copyright notice
- Disclose source code of any modified version
- Disclose source code if used to provide a network service
- License any derivative works under **AGPL-3.0**

See the full license text in: [`LICENSE`](./LICENSE)

### ⚠️ Disclaimer

**USE AT YOUR OWN RISK.** PruneMate is provided "as is" without warranty of any kind. The author(s) and contributors are not responsible for:
- Data loss from pruned Docker resources
- Service interruptions or downtime
- System instability or performance issues
- Any damages resulting from the use or misuse of this software

Always:
- ✅ Understand which resources will be deleted
- ✅ Keep backups of important data and configurations
- ✅ Review logs after prune operations
- ✅ Start with conservative settings

© 2025 – PruneMate Project

---

<p align="center">
  <strong>Keep your Docker host clean with PruneMate! 🐳🧹</strong>
</p>
