# PruneMate Architecture & Design

This document provides a detailed visual representation of PruneMate's internal architecture and workflow.

## System Architecture

```mermaid
flowchart TD
    Start([PruneMate]) --> Auth{Auth<br/>Enabled?}
    Auth -->|No| WebUI[Web UI<br/>Port 8080]
    Auth -->|Yes| Login[Login Page<br/>Session Auth]
    Login -->|Authenticated| WebUI
    Login -->|API Client| BasicAuth[Basic Auth<br/>Fallback]
    BasicAuth -->|Valid| WebUI
    
    Start --> Scheduler[Scheduler<br/>every minute]
    Start --> API[API Endpoints<br/>/api/stats]
    
    WebUI --> |Configure| Config[(config.json<br/>• Schedule<br/>• Prune options<br/>• Notifications<br/>• Remote hosts)]
    WebUI --> |View Stats| StatsUI[Display stats.json<br/>All-time metrics]
    WebUI --> |Manual/Preview| Manual[Manual Trigger]
    API --> |Homepage Widget| StatsUI
    
    Scheduler --> CheckTime{Scheduled<br/>time?}
    CheckTime --> |No| Scheduler
    CheckTime --> |Yes| LoadConfig[Load Config]
    
    Manual --> |Preview| Preview[Get Preview<br/>Per-host breakdown<br/>Show resources]
    Preview --> |User confirms| LoadConfig
    
    LoadConfig --> Lock{Already<br/>running?}
    Lock --> |Yes| Skip[Skip]
    Lock --> |No| CheckHosts{Remote<br/>hosts?}
    
    CheckHosts --> |Yes| Remote[Local + Remote Hosts<br/>via docker-socket-proxy<br/>tcp://host:2375]
    CheckHosts --> |No| Local[Local Host Only<br/>unix:///var/run/docker.sock]
    
    Remote --> CheckOptions
    Local --> CheckOptions
    
    CheckOptions{Check enabled<br/>prune options}
    CheckOptions --> |Containers ✓| PruneC[Prune Containers<br/>stopped/exited]
    CheckOptions --> |Images ✓| PruneI[Prune Images<br/>all unused]
    CheckOptions --> |Networks ✓| PruneN[Prune Networks<br/>unused]
    CheckOptions --> |Volumes ✓| PruneV[Prune Volumes<br/>all unused + named]
    CheckOptions --> |Build Cache ✓| PruneB[Prune Build Cache<br/>Docker builder cache]
    
    PruneC --> Aggregate
    PruneI --> Aggregate
    PruneN --> Aggregate
    PruneV --> Aggregate
    PruneB --> Aggregate
    
    Aggregate[Aggregate Results<br/>Space + Counts] --> Stats[Update stats.json<br/>• Total runs<br/>• Resources deleted<br/>• Space reclaimed<br/>• Timestamps]
    
    Stats --> Notify{Notifications<br/>enabled?}
    
    Notify --> |Yes + Changes| Send[Send Notification<br/>Gotify/ntfy/Discord/Telegram<br/>Per-host breakdown]
    Notify --> |No or No changes| Log[Write to<br/>prunemate.log]
    Send --> Log
    Log --> Done[Done]
    
    style Start fill:#4a90e2
    style WebUI fill:#50c878
    style Scheduler fill:#9b59b6
    style Config fill:#f39c12
    style CheckOptions fill:#e74c3c
    style Stats fill:#16a085
    style Send fill:#3498db
    style Preview fill:#e67e22
    style API fill:#2ecc71
    style Remote fill:#8e44ad
```

## Component Descriptions

### Core Components

- **Web UI (Port 8080)**: Flask-based web interface for configuration and manual operations
- **Scheduler**: APScheduler running every minute to check if prune should execute
- **API Endpoints**: REST API for external integrations (e.g., Homepage dashboard)

### Configuration & State

- **config.json**: Persistent configuration including schedule, prune options, notifications, and remote hosts
- **stats.json**: Cumulative all-time statistics (space reclaimed, resources deleted, timestamps)
- **prunemate.lock**: File lock to prevent concurrent prune operations
- **last_run_key**: Tracks last successful scheduled run to prevent duplicates

### Prune Operations

- **Containers**: Removes stopped/exited/dead containers
- **Images**: Removes ALL unused images (not just dangling) using `filters={"dangling": False}`
- **Networks**: Removes unused networks (excluding default bridge/host/none)
- **Volumes**: Removes ALL unused volumes including named volumes using `filters={"all": True}`
- **Build Cache**: Removes Docker builder cache (can reclaim significant space, 10GB+)

### Multi-Host Support

- **Local Host**: Direct access via `unix:///var/run/docker.sock`
- **Remote Hosts**: Secure access via docker-socket-proxy at `tcp://host:2375`
- **Per-host Results**: Separate statistics and error handling for each host

### Notification Flow

- **Providers**: Gotify (self-hosted), ntfy.sh (pub-sub), Discord (webhooks), or Telegram (Bot API)
- **Authentication**: 
  - Gotify: App tokens
  - ntfy: Bearer tokens, Basic Auth, or unauthenticated
  - Discord: Webhook URLs
  - Telegram: Bot Token + Chat ID
- **Priority System**: Text-based (Low/Medium/High) with provider-specific behavior
  - Gotify: Numeric mapping (Low=2, Medium=5, High=8)
  - ntfy: Numeric mapping (Low=2, Medium=3, High=5)
  - Discord: Color mapping (Low=Green, Medium=Orange, High=Red)
  - Telegram: Notification sound (Low=Silent, Medium/High=Sound)
- **Smart Notifications**: Optional "only on changes" mode to reduce noise
- **Per-host Breakdown**: Detailed results for each Docker host in multi-host setups

## Workflow Explanation

1. **Trigger Sources**:
   - Scheduled: Minute-based scheduler checks if current time matches configured schedule
   - Manual: User clicks "Run now" after optionally previewing resources

2. **Preview Mode** (Manual only):
   - Queries each Docker host for unused resources
   - Shows detailed lists of what would be deleted
   - User must confirm before actual execution
   - Checkbox states auto-save when switching between preview and settings

3. **Execution**:
   - Acquires file lock to prevent concurrent runs
   - Loads latest configuration from disk
   - Connects to local and/or remote Docker hosts
   - Executes enabled prune operations per host
   - Aggregates results across all hosts

4. **Post-Execution**:
   - Updates cumulative statistics in stats.json
   - Sends notifications if enabled (respects "only on changes" setting)
   - Logs detailed results with timezone-aware timestamps
   - Releases file lock

## File Structure

```
/config/
├── config.json          # User configuration (persistent)
├── stats.json           # All-time statistics (cumulative data)
├── prunemate.lock       # Prevents concurrent runs
└── last_run_key         # Tracks last successful run

/var/log/
└── prunemate.log        # Application logs (rotating, 5MB max)
```

---

For more information, see the main [README.md](README.md).
