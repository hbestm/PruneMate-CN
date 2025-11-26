# PruneMate

<p align="center">
  <img width="400" height="400" alt="prunemate-logo" src="https://github.com/user-attachments/assets/0785ea56-88f6-4926-9ae1-de736840c378" />
</p>

<h1 align="center">PruneMate</h1>
<p align="center"><em>Docker image & resource cleanup helper, on a schedule!</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.2-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/docker-compose-0db7ed?style=flat-square"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square"/>
</p>

A sleek, lightweight web interface to **automatically clean up Docker resources** on a schedule. Built with Python (Flask) · Docker SDK · APScheduler · Gunicorn

**Keep your Docker host tidy with scheduled cleanup of unused images, containers, networks, and volumes.**


---

## ✨ Features

- 🕐 **Flexible scheduling** - Daily, Weekly, or Monthly cleanup runs
- 🌍 **Timezone aware** - Configure your local timezone
- 🕒 **12/24-hour time format** - Choose your preferred time display
- 🧹 **Selective cleanup** - Choose what to prune: containers, images, networks, volumes
- 🔔 **Smart notifications** - Gotify or ntfy.sh support with optional change-only alerts
- 🎨 **Modern UI** - Dark theme with smooth animations and responsive design
- 🔒 **Safe & controlled** - Manual trigger option and detailed logging
- 📊 **Detailed reports** - See exactly what was cleaned and how much space was reclaimed

---

## 📷 Screenshots

### Main Dashboard
The overall look and feel of the PruneMate dashboard
<p align="center">
  <img width="400" height="700" src="https://github.com/user-attachments/assets/3e9a6fc0-01c3-4da2-a095-d6f9480d4416" /> 
</p>

### Main Dashboard - Schedule Configuration
Configure when and how often PruneMate should clean up your Docker resources.

<p align="center">
  <img width="400" height="400" alt="prunemate-schedule" src="https://github.com/user-attachments/assets/3a822897-5ede-4476-b570-f4d8adf37867" /> 
</p>

### Cleanup Options & Settings
Select which Docker resources to clean up and configure advanced options.

<p align="center">
  <img width="400" height="400" alt="prunemate-cleanup" src="https://github.com/user-attachments/assets/70ae1e8f-49a1-4c89-ac46-685d804ee3db" />
</p>

### Notification Settings
Set up notifications via Gotify or ntfy.sh to stay informed about cleanup results.

<p align="center">
  <img width="400" height="400" alt="prunemate-notifications" src="https://github.com/user-attachments/assets/4a6be018-588e-4596-871c-1b35a92a7deb" /> 
</p>

<p align="center">
  <img width="400" height="400" alt="prunemate-notifications" src="https://github.com/user-attachments/assets/73a06c4d-fffa-40eb-a010-239d7d364004" /> 
</p>


### Cleanup Results
Get detailed statistics notifications about what was cleaned and how much space was reclaimed.

Gotify :
<p align="center">
  <img width="400" height="400" alt="prunemate-results" src="https://github.com/user-attachments/assets/26c1eccb-96c1-4385-8a1a-ef8c4587909e" /> 
</p>

ntfy :
<p align="center">
  <img width="400" height="400" alt="prunemate-results" src="https://github.com/user-attachments/assets/232acb54-b06f-46b7-b829-df7a10dd4a6a" />
</p>


---

## 🐳 Docker Compose Configuration

`docker-compose.yaml`:

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
5. **Sends notification** (if configured and enabled)
6. **Logs everything** with timezone-aware timestamps

### File Structure

```
/config/
├── config.json          # Your configuration (persistent)
├── prunemate.lock       # Prevents concurrent runs
└── last_run_key         # Tracks last successful run

/var/log/
└── prunemate.log        # Application logs (rotating, 5MB max)
```

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
   - **URL:** `https://ntfy.sh` (your self-hosted instance)
   - **Topic:** Your chosen topic name

**Subscribe to notifications:**
- **Web:** Visit `https://ntfy.sh/your-topic`
- **Mobile:** Install the ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)) and subscribe to your topic
- **Desktop:** Use ntfy desktop app or web browser


---

## 🧠 Troubleshooting

| Problem | Solution |
|---------|----------|
| ❌ Can't access web interface | • Check if port 7676 is available and not blocked by firewall<br>• Verify container is running: `docker ps`<br>• Check logs: `docker logs prunemate` |
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

## 📝 Changelog

### Version 1.2.2 (November 2025)
- ✨ Added 12/24-hour time format support via `PRUNEMATE_TIME_24H` environment variable
- 🌍 Improved timezone handling across all components (logs, scheduling, notifications)
- 🎨 Enhanced UI with custom time picker for 12-hour mode (hour 1-12, minutes, AM/PM selector)
- 🐛 Fixed config synchronization issues in multi-worker setup
- ⚡ Simplified architecture: reduced from 2 workers to 1 for better reliability
- 📝 Implemented silent config loading to reduce log noise
- 🔧 Improved input validation with instant clamping and 2-digit limits
- 🔒 Added thread-safe configuration saving with file locking

### Version 1.2.1 (November 2025)
- 🐛 Fixed scheduler not triggering at configured times
- 🔄 Config now reloads before each scheduled check to ensure synchronization
- 🔒 Added thread-safe config saving mechanism
- 📊 Improved logging with timezone-aware timestamps

### Version 1.2.0 (November 2025)
- 🔔 Added notification support (Gotify & ntfy.sh)
- 🎨 Complete UI redesign with modern dark theme
- 📊 Enhanced statistics and detailed cleanup reporting
- 🎯 Added "only notify on changes" option
- 🔘 Improved button animations and hover effects

### Version 1.1.0 (October 2025)
- 🎉 Initial release
- 🕐 Daily, Weekly, and Monthly scheduling
- 🧹 Selective cleanup options (containers, images, networks, volumes)
- 🌐 Web interface for configuration
- 📁 Persistent configuration and logging

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

**License:** MIT License  
© 2025 – PruneMate Project

---

<p align="center">
  <strong>Keep your Docker host clean with PruneMate! 🐳🧹</strong>
</p>
