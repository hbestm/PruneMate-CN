# Changelog

All notable changes to PruneMate will be documented in this file.


### Added
- 🔐 **Optional authentication system** - Secure password protection for web interface and API
  - Form-based login with styled page matching app design
  - Scrypt password hashing (32768 iterations, industry standard)
  - Base64-encoded hashes to prevent Docker Compose from interpreting `$` as environment variables
  - Built-in hash generator: `docker run --rm anoniemerd/prunemate python prunemate.py --gen-hash "password"`
  - Session management with secure HttpOnly cookies
  - Basic Auth fallback for API clients (Homepage, Dashy, etc.)
  - Logout button in dashboard top-right corner
  - Opt-in design: only enabled when `PRUNEMATE_AUTH_PASSWORD_HASH` is set
  - Backward compatible: runs in open mode without auth variables
  - New environment variables: `PRUNEMATE_AUTH_USER` (default: admin), `PRUNEMATE_AUTH_PASSWORD_HASH`
- 🏗️ **Docker build cache pruning support** - New option to clean up Docker builder cache
  - Can reclaim significant disk space
  - Uses Docker API's `/build/prune` endpoint
  - Integrated into preview, statistics, and notifications
  - **⚠️ IMPORTANT: Docker Socket Proxy users MUST add `BUILD=1` environment variable to enable this feature**
  - See README for updated Docker Socket Proxy configuration
- 💬 **Discord notification provider** - Full support for Discord webhook notifications
  - Configure via Webhook URL (from Discord server integrations)
  - Priority-based color coding: Low=Green, Medium=Orange, High=Red
  - Rich embed formatting with timestamps
  - Works alongside Gotify, ntfy, and Telegram providers
- 📱 **Telegram notification provider** - Full support for Telegram Bot notifications
  - Priority support: Low=silent notifications, Medium/High=normal sound
  - HTML formatting for rich message display
  - Works alongside Gotify, ntfy, and Discord providers
- 🎯 **Text-based priority system** - Changed from numeric (1-10) to text-based (Low/Medium/High)
  - More intuitive and user-friendly
  - Default priority changed from "Low" to "Medium"
  - Automatic migration from numeric to text priority on upgrade
  - Provider-specific priority mapping (e.g., Telegram uses disable_notification, Gotify uses numeric values)

### Changed
- ⚙️ **Default notification priority** - Changed from "Low" to "Medium" for better visibility
  - All new configurations default to medium priority
  - Existing configurations with numeric priorities auto-migrate to text equivalents
  - Migration logic: 1-3→Low, 4-7→Medium, 8-10→High

### Fixed
- 🔧 **Notification provider migration** - Added forward compatibility for new providers
  - Discord and Telegram credentials automatically added to existing configs
  - All provider subkeys (gotify, ntfy, discord, telegram) guaranteed to exist
  - Prevents errors when upgrading from older versions

## [V1.2.8] - December 2025

### Added
- 🔍 **Prune preview before manual execution** - See exactly what will be deleted before running manual prune
  - Shows detailed list of containers, images, networks, and volumes to be removed
  - Per-host breakdown for multi-host setups
  - Two-step confirmation process for safer manual pruning
  - Only applies to manual "Run now" executions (scheduled runs remain automatic)
  - Auto-save functionality: checkbox states persist when switching between preview and settings
- 🏠 **Homepage dashboard integration** - New `/api/stats` endpoint for Homepage widget support
  - Returns all-time statistics in customapi-compatible format
  - Includes human-readable space reclaimed field (`spaceReclaimedHuman`)
  - Relative time formatting for last run (`lastRunText` shows "2h ago", "3d ago", etc.)
  - Easy integration with Homepage dashboard services

### Improved
- 🧹 **Image prune behavior** - Now removes ALL unused images (not just dangling)
  - Uses `filters={"dangling": False}` for comprehensive cleanup
  - Matches preview display with actual prune behavior
  - More aggressive space reclamation while maintaining safety
- 📦 **Volume prune behavior** - Explicitly includes named volumes
  - Uses `filters={"all": True}` to remove all unused volumes
  - Named volumes are pruned alongside anonymous volumes
  - Preview accurately shows all volumes to be removed

### Fixed
- 🐛 **Checkbox reading bug** - Preview modal now correctly reads checkbox states
  - Added missing `id` attributes to all four checkboxes
  - JavaScript `getElementById()` now works correctly
  - Fixed "No prune options selected" error when checkboxes were checked
- 🐛 **JavaScript variable scope** - Fixed redeclaration errors in time formatting
  - Resolved Jinja2 template variable conflicts in 12h/24h time display
  - Cleaner variable naming for better maintainability

---

## [V1.2.7] - December 2025

### Added
- 🔐 **ntfy authentication support** - Bearer token and Basic Auth (username:password in URL)
  - Priority system: Bearer token → Basic Auth → unauthenticated
  - RFC 3986 compliant URL parsing for embedded credentials
  - Optional token field in UI for ntfy provider
- 🔒 **Enhanced credential security** - Passwords and tokens masked in all log output
  - URL credentials (username:password) redacted in logs
  - Bearer tokens sanitized in notification logs

### Improved
- 🎨 **Logo enhancement** - Improved SVG logo design (thanks to [@shollyethan](https://github.com/shollyethan)) + added to the Self-Hosted Dashboard Icons on https://selfh.st/icons/
- 📏 Logo size increased from 76×76px to 82×82px for better visibility
- 📱 **Better mobile support** - Enhanced responsive design for smartphone usage
- 🔔 Notification panel height increased to 900px with enhanced scrolling behavior
- 🔧 **Config migration improvements** - Deep merge strategy for nested structures
  - Prevents data loss during v1.2.6 → v1.2.7 upgrades
  - Preserves both gotify and ntfy settings in nested notifications structure
- 📊 **Stats persistence improvements** - Forward-compatible field migration
  - Type-safe increments with defensive programming
  - Graceful handling of corrupt or incomplete stats files
- 🏗️ **Hosts API consistency** - Local socket now included in `/hosts` endpoint response

### Fixed
- 🐛 Config shallow merge bug causing nested key loss during upgrades
  - Replaced `dict.update()` with recursive `_deep_merge()` function
- 🐛 Legacy notification migration incomplete (only migrated gotify, missed ntfy)
- 🐛 Stats field migration missing for new fields in future versions
- 🐛 Stats type safety issues with corrupt JSON files
- 🐛 Notification panel button visibility on smaller screens

---

## [V1.2.6] - November 2025

### Added
- 🐳 **Multi-host support** - Manage multiple Docker hosts from one interface
  - Per-host results in notifications with detailed breakdown for each Docker host
  - Docker hosts management UI (add, edit, enable/disable, delete external hosts)

### Improved
- 🔔 Notification formatting with enhanced layout, consistent emoji usage, and bullet points
- 📬 Notifications now show per-host breakdown for multi-host setups with aggregate totals
- 🎯 Better visual hierarchy in notifications with clear sections and spacing
- 🔧 Code quality improvements and better error handling

### Fixed
- 🐛 Critical checkbox handling bug affecting all prune and notification toggles

---

## [V1.2.5] - November 2025

### Improved
- 🔧 Eliminated duplicate code - moved `_validate_time()` to module level
  - Removed identical function definitions from `/update` and `/test-notification` routes
  - Renamed to `validate_time()` as public module-level function
- 📝 Better log clarity for prune operations
  - Volumes: "Pruning volumes (unused anonymous volumes only)…"
- 🧹 Moved `calendar` import from inline to top-level imports

### Fixed
- 🐛 Monthly schedule bug where jobs never ran in shorter months
  - Jobs configured for day 30-31 now run on last day of shorter months (e.g., Feb 28/29)
  - Uses `calendar.monthrange()` to determine actual last day of each month
- 🐛 Configuration deep copy bug causing shared nested dictionaries
  - All `.copy()` operations replaced with proper deep copy via `json.loads(json.dumps())`
  - Prevents config corruption when modifying nested notification settings
  - Fixed in 4 locations: initialization + 3 in `load_config()`
- 🐛 KeyError in legacy Gotify config migration
  - Now safely checks if notifications dict exists before accessing nested keys
  - Uses `.get()` with fallback values to prevent crashes on old config files

---

## [V1.2.4] - November 2025

### Added
- 📊 **All-Time Statistics dashboard** showing cumulative prune data
  - Total space reclaimed across all runs
  - Counters for containers, images, networks, volumes deleted
  - Total prune runs with first/last run timestamps
  - Statistics persist in `/config/stats.json`

### Improved
- 📝 All functions now have proper Python docstrings for better IDE support
- 🔧 Code quality improvements and better error handling

### Fixed
- 🐛 12-hour time format backend handling in `/update` and `/test-notification` routes
- 🐛 Minute display now shows leading zeros (e.g., "7:04" instead of "7:4")
- 🐛 Time input validation now runs on page load (`initTimeClamp()`)

---

## [V1.2.3] - November 2025

### Added
- 🏗️ ARM64 architecture installation instructions (Apple Silicon, ARM servers, Raspberry Pi)

### Improved
- 📜 License changed from MIT to AGPLv3
- 📝 All functions documented in English for better code maintainability
- 📚 Documentation improvements with Quick Start guide

---

## [V1.2.2] - November 2025

### Added
- ✨ 12/24-hour time format support via `PRUNEMATE_TIME_24H` environment variable
- 🎨 Custom time picker for 12-hour mode (hour 1-12, minutes, AM/PM selector)

### Improved
- 🌍 Timezone handling across all components (logs, scheduling, notifications)
- ⚡ Simplified architecture: reduced from 2 workers to 1 for better reliability
- 📝 Silent config loading to reduce log noise
- 🔧 Input validation with instant clamping and 2-digit limits

### Fixed
- 🐛 Config synchronization issues in multi-worker setup
- 🔒 Thread-safe configuration saving with file locking

---

## [V1.2.1] - November 2025

### Improved
- 🔒 Thread-safe config saving mechanism
- 📊 Logging with timezone-aware timestamps

### Fixed
- 🐛 Scheduler not triggering at configured times
- 🔄 Config reloads before each scheduled check to ensure synchronization

---

## [V1.2.0] - November 2025

### Added
- 🔔 Notification support (Gotify & ntfy.sh)
- 🎯 "Only notify on changes" option
- 📊 Enhanced statistics and detailed cleanup reporting

### Improved
- 🎨 Complete UI redesign with modern dark theme
- 🔘 Improved button animations and hover effects

---

## [V1.1.0] - October 2025

### Added
- 🎉 Initial release
- 🕐 Daily, Weekly, and Monthly scheduling
- 🧹 Selective cleanup options (containers, images, networks, volumes)
- 🌐 Web interface for configuration
- 📁 Persistent configuration and logging
