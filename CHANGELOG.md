# Changelog

All notable changes to PruneMate will be documented in this file.

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
