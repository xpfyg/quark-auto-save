# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

夸克网盘自动转存 (Quark Auto Save) - An automated system for Quark cloud drive that handles daily check-ins, automatic file transfers, file renaming/organization, notifications, and media library refreshing.

**Primary use case**: Automatically track and transfer continuously updating shared resources to your own Quark drive, with optional Emby media library integration.

## Core Architecture

### Main Components

1. **quark_auto_save.py** - Core automation script
   - `Quark` class: Handles all Quark cloud drive API interactions (authentication, file operations, sharing)
   - `Emby` class: Optional Emby media library integration for automatic refresh after updates
   - Task execution flow: Sign-in → Transfer → Rename → Notify → Emby refresh

2. **app/run.py** - Flask web UI server
   - WebUI for configuration management
   - APScheduler for cron-based task scheduling
   - Server-Sent Events (SSE) for real-time script execution output
   - Session-based authentication

3. **Configuration System**
   - `quark_config.json`: Main config file (cookie, tasks, Emby, notifications, crontab)
   - Environment variables: `WEBUI_USERNAME`, `WEBUI_PASSWORD`, `QUARK_COOKIE`, `GH_PROXY`
   - WebUI config location: `./config/quark_config.json`

4. **Database Layer** (Custom Addition)
   - `db.py`: SQLAlchemy connection to MySQL
   - `model/user_video.py`: UserVideo model for tracking shared videos
   - Note: Contains hardcoded credentials - should be moved to environment variables

### Task Processing Flow

1. **Initialization**: Verify accounts via cookie, get account info
2. **Sign-in**: Daily check-in to earn storage space
3. **Directory Setup**: Create target directories if they don't exist, cache fid mappings
4. **File Transfer Loop**: For each task:
   - Parse share URL to extract pwd_id and pdir_fid
   - Validate share link (get stoken) - marks failed shares as banned
   - Get source file list from share, get target directory list
   - Apply regex pattern matching to filter files
   - Check for existing files (with optional extension ignoring)
   - Transfer new files, wait for async transfer completion
   - Optionally rename files based on regex replace rules
   - Support recursive subdirectory updates via `update_subdir`
5. **Emby Integration**: Search and refresh media library if configured
6. **Notifications**: Send results via configured push channels

### Key Features

- **Magic Regex**: Special patterns like `$TV` that expand to predefined regex (90% TV show compatibility)
- **Extension Ignoring**: Match files regardless of extension (useful for format changes)
- **Subdirectory Recursion**: Update nested folders matching patterns
- **Task Scheduling**: Supports end dates and specific weekdays via `runweek`
- **Multi-account**: Multiple cookies supported (only first account does transfers, others sign-in only)

## Development Commands

### Running Locally

```bash
# Run standalone script (CLI mode)
python3 quark_auto_save.py [config_path] [task_index]

# Run WebUI server
python3 app/run.py
# Access at http://localhost:5005
```

### Docker Deployment

```bash
# Build
docker build -t quark-auto-save .

# Run
docker run -d \
  --name quark-auto-save \
  -p 5005:5005 \
  -e WEBUI_USERNAME=admin \
  -e WEBUI_PASSWORD=admin123 \
  -v ./quark-auto-save/config:/app/config \
  -v /etc/localtime:/etc/localtime \
  cp0204/quark-auto-save:latest
```

### Testing

The config includes test tasks with valid share links:
```bash
# Test all tasks
python3 quark_auto_save.py

# Test specific task by index
python3 quark_auto_save.py quark_config.json 0
```

## Important Patterns

### Quark API Authentication
- Cookie must include `__pus`, `__kp`, `__kps`, `__ktd`, `__uid` and other session tokens
- Extract `st` token from cookie for `x-clouddrive-st` header
- Use mobile login with SMS verification for complete cookies

### File ID Management
- Files/folders identified by `fid` (file ID)
- Share links contain `pwd_id` and optional `pdir_fid` (parent directory fid)
- Cache directory fid mappings in `savepath_fid` dict to avoid repeated lookups
- Root directory is always fid "0"

### Async Transfer Pattern
- `save_file()` returns task_id, not final result
- Must poll `query_task()` with increasing retry_index until status != 0
- Wait 500ms between polls, print progress dots

### Regex in JSON Config
- JSON requires double-escaping: `\d` → `\\d`, `\.` → `\\.`
- Pattern matching uses Python `re` module
- Replace uses backreferences: `\1` in Python → `\\1` in JSON

## Configuration Notes

### Task Object Structure
```json
{
  "taskname": "Name for notifications and Emby search",
  "shareurl": "https://pan.quark.cn/s/{pwd_id}#/list/share/{pdir_fid}-folder",
  "savepath": "/target/directory",
  "pattern": "regex to match files",
  "replace": "regex replacement (empty = no rename)",
  "enddate": "YYYY-MM-DD (optional)",
  "emby_id": "force Emby ID or 0 to skip",
  "ignore_extension": true,
  "runweek": [1,2,3,4,5,6,7],
  "update_subdir": "regex for recursive folder updates",
  "shareurl_ban": "Auto-set when share link fails"
}
```

### Notification System
- Uses `notify.py` module (compatible with Qinglong notifications)
- Falls back to environment variables if `push_config` not set
- `QUARK_SIGN_NOTIFY`: Control sign-in success notifications

### Custom Database Functions
- `all_share()`: Batch create shares from a directory
- `save_share_to_db()`: Sync share list to database
- `batch_set_status()`: Update share status from audit results
- `batch_set_title()`: Clean and normalize titles

## Code Style Notes

- Chinese comments and print statements throughout
- Emoji used in console output (📅, 👤, ✅, ❌, 📢, 🎞, 📁)
- Global variables: `CONFIG_DATA`, `NOTIFYS`, `GH_PROXY`, `MAGIC_REGEX`
- Qinglong environment detection via config file existence

## Security Warnings

⚠️ **Configuration Management**:
- Database credentials now use environment variables (see `.env.example`)
- All sensitive config should be in `.env` file (not committed to git)
- `.gitignore` updated to exclude `.env` files

**Setup Required**:
```bash
# Copy template and configure
cp .env.example .env
vim .env  # Fill in real credentials

# Test database connection
python3 test_db.py
```

**Environment Variables**:
- `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_DATABASE`
- `QUARK_COOKIE` - Quark cloud drive authentication
- `TMDB_API_KEY` - Optional, for movie/TV metadata

## Database Architecture

### New Database Layer (Custom Addition)

**Files**:
- `db.py`: SQLAlchemy connection with connection pooling
- `model/cloud_resource.py`: Cloud resource tracking model
- `model/tmdb.py`: TMDB movie/TV metadata model
- `resource_manager.py`: Resource management with auto-save and TMDB integration

**Database Tables**:
- `cloud_resource`: Tracks shared resources (drama_name, link, expiry, TMDB association)
- `tmdb`: Stores TMDB metadata (title, year, poster, description)

**Key Features**:
- Connection pooling (QueuePool, size=5)
- Thread-safe sessions (scoped_session)
- Auto-reconnect on connection loss (pool_pre_ping)
- UTF8MB4 support for Chinese and emoji

**Initialization**:
```bash
# Create tables
mysql -u root -p < init_database.sql

# Test connection
python3 test_db.py
```

## Security Best Practices

⚠️ **Remaining Issues in quark_auto_save.py**:
- Cookie values hardcoded in utility functions (lines 963, 987, 1007 in quark_auto_save.py)
- Flask secret key is static (app/run.py:43)

**Before committing**: Remove hardcoded cookies and replace Flask secret key with environment variable.

## Deployment Targets

- **Qinglong**: Use `ql repo` command, script-only mode
- **Docker**: Full WebUI + scheduled tasks
- **Standalone**: Manual execution via Python

## External Dependencies

- **treelib**: Display hierarchical file trees in notifications
- **flask**: WebUI server
- **apscheduler**: Cron scheduling
- **requests**: HTTP client for Quark API
- **notify**: Push notification module (included)
- **pymysql**, **sqlalchemy**: Database integration (optional)
