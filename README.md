# PocketBase Setup Tools

A comprehensive Python toolkit for automating PocketBase project initialization with TypeScript hooks support.

## Overview

`pb_setup` is an automated setup script that creates a complete PocketBase development environment with:
- Automatic binary download and caching
- TypeScript hooks project configuration
- Project folder structure initialization
- Automated helper scripts
- Port configuration support

## Installation

The script is already symlinked to your PATH:

```bash
pb_setup
```

Or use the full path:

```bash
python3 ~/WorkStation/ME/pb_tools/pb_setup.py
```

## Quick Start

### Mode 1: Interactive (Default)

```bash
pb_setup
```

The script will prompt you for all parameters:
1. **Project Location** - Where to create your PocketBase project
2. **Port Configuration** - Default is 8090 (can be customized)
3. **Version Selection** - Choose from available PocketBase versions

### Mode 2: With Arguments

Provide parameters directly without prompts:

```bash
# Create project with all settings
pb_setup ~/my_project --version v0.30.3 --port 3000
```

Or mix interactive and arguments:

```bash
# Create with specific port, choose version interactively
pb_setup ~/my_project --port 3000
```

## Features

### ✅ Automatic Project Setup

- Creates complete folder structure
- Downloads appropriate PocketBase binary for your OS/architecture
- Sets up TypeScript hooks project with proper configuration
- Generates helper scripts and documentation

### ✅ Port Configuration

- Prompts for custom port during setup (default: 8090)
- Validates port range (1024-65535)
- Saves configuration to `pb_config.json`
- Supports runtime port override

### ✅ Binary Caching

- Downloads cached in `~/.pb_cache/`
- Prevents re-downloading on subsequent setups
- Supports macOS (Intel & ARM64), Linux, and Windows

### ✅ TypeScript Hooks

- Pre-configured TypeScript project in `pb_hooks_ts/`
- tsup bundler for compilation
- ES5 target with ES2015 modules (PocketBase compatible)
- Example hooks template included

### ✅ Helper Scripts

**run.sh** - Launch PocketBase
```bash
./run.sh                    # Use configured port
./run.sh --port 3000        # Override port at runtime
```

**init-types.sh** - Initialize TypeScript types (first time only)
```bash
./init-types.sh
```

## Project Structure

After setup, your project contains:

```
project_folder/
├── pocketbase              # PocketBase binary
├── pb_config.json          # Configuration (port, version)
├── pb_data/                # Data directory
├── pb_hooks/               # Compiled JavaScript hooks
├── pb_hooks_ts/            # TypeScript hooks source
│   ├── src/
│   │   ├── entries/        # Hook files (main.pb.ts)
│   │   ├── types/          # TypeScript definitions
│   │   └── lib/            # Shared utilities
│   ├── package.json        # Dependencies
│   ├── tsconfig.json       # TypeScript config
│   └── tsup.config.ts      # Build configuration
├── pb_migration/           # Database migrations
├── pb_public/              # Static files
├── .gitignore              # Git configuration
├── run.sh                  # Launch script
├── init-types.sh           # Type initialization script
└── README.md               # Project documentation
```

## Usage Workflow

### 1. Create New Project

```bash
pb_setup
# Follow prompts to select location, port, and version
```

### 2. Initialize TypeScript Types (First Time Only)

```bash
cd your_project
./init-types.sh
```

This launches PocketBase once to generate types, then copies them to your TypeScript project.

### 3. Install Dependencies

```bash
cd pb_hooks_ts
npm install
```

### 4. Compile Hooks

```bash
npm run build      # Single build
npm run dev        # Watch mode (auto-recompile)
```

### 5. Launch PocketBase

```bash
cd ..
./run.sh
```

Access the admin panel at: **http://localhost:8090** (or your configured port)

## Command Reference

### Usage

```
pb_setup [PROJECT_DIR] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `PROJECT_DIR` | Path to project folder | No (will prompt if not provided) |

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--version` | PocketBase version to download | `--version v0.30.3` |
| `--port` | Port for PocketBase (1024-65535) | `--port 3000` |
| `-h, --help` | Show help message | `pb_setup -h` |

### Examples

```bash
# Interactive mode - prompts for everything
pb_setup

# Create in specific folder, interactive for version and port
pb_setup ~/my_project

# All parameters from command line
pb_setup ~/my_project --version v0.30.3 --port 3000

# Only version specified
pb_setup ~/my_project --version v0.30.3

# Only port specified
pb_setup ~/my_project --port 8091

# Show help
pb_setup -h
pb_setup --help
```

## Port Configuration

### During Setup
```
🔌 Configuration du port

   Port par défaut: 8090
   Appuyez sur Entrée pour conserver le port par défaut ou tapez un nouveau port: 3000
✅ Port configuré: 3000
```

### At Runtime
```bash
./run.sh --port 8091      # Temporarily use port 8091
```

### View Configuration
```bash
cat pb_config.json
# {
#   "port": 3000,
#   "version": "v0.30.3"
# }
```

## TypeScript Hooks Development

### Create a New Hook File

Create `pb_hooks_ts/src/entries/users.pb.ts`:

```typescript
/// <reference path="../types/pocketbase.d.ts" />

onRecordAfterCreateRequest((e) => {
  console.log("New user created:", e.record.getId());
}, "users");
```

### Compile

```bash
cd pb_hooks_ts
npm run build
```

Compiled files appear in `pb_hooks/`

### Share Code Between Hooks

Place reusable code in `src/lib/`:

```typescript
// src/lib/utils.ts
export function formatDate(date: Date): string {
  return date.toISOString();
}

// src/entries/main.pb.ts
import { formatDate } from '../lib/utils';
console.log(formatDate(new Date()));
```

## Binary Caching

Downloaded binaries are cached in `~/.pb_cache/`

### Clean Cache

```bash
rm -rf ~/.pb_cache/
```

## System Requirements

- **Python 3.6+**
- **npm/yarn** (for TypeScript development)
- **Bash** (for helper scripts)
- **macOS, Linux, or Windows**

## Environment Variables

None required, but the script uses:

- `HOME` - For cache directory
- `PATH` - For npm command lookup

## Troubleshooting

### Port Already in Use

Use `--port` argument to specify a different port:

```bash
./run.sh --port 3000
```

### Types Not Generated

If `init-types.sh` fails:

```bash
# Manual type generation
./pocketbase serve --dir=pb_data &
sleep 3
kill %1
cp pb_data/types.d.ts pb_hooks_ts/src/types/pocketbase.d.ts
```

### Binary Download Failed

Clear cache and retry:

```bash
rm -rf ~/.pb_cache/
pb_setup
```

### npm install Fails in pb_hooks_ts

Check Node.js version:

```bash
node --version  # Requires v14+
npm --version
```

## Advanced Configuration

### Custom TypeScript Settings

Edit `pb_hooks_ts/tsconfig.json` to adjust compilation settings.

### Custom Build Configuration

Edit `pb_hooks_ts/tsup.config.ts` to change bundler behavior.

## Resources

- **PocketBase Documentation** - https://pocketbase.io/docs/
- **JS Event Hooks** - https://pocketbase.io/docs/js-overview/
- **TypeScript** - https://www.typescriptlang.org/
- **tsup** - https://tsup.egoist.dev/

## Support

For issues or questions:

1. Check the generated project's README.md
2. Review PocketBase documentation
3. Verify TypeScript configuration

## Version History

### v1.0.0 (Current)

- Full automated PocketBase project setup
- Port configuration support
- Binary caching system
- TypeScript hooks scaffolding
- Helper scripts (run.sh, init-types.sh)
- Comprehensive documentation

## License

This tool is provided as-is for PocketBase project setup automation.
