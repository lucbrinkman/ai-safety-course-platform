# Dev Server Management Design

## Problem

Multiple issues with dev server management across workspaces:

1. **Cross-workspace kills**: When Claude kills a server using `pkill -f "python main.py"`, it kills ALL instances across all workspaces, not just the current one.

2. **Orphaned servers**: Dev servers sometimes remain running after Claude sessions end.

3. **Manual port configuration**: CLAUDE.md instructions specify which ports to use per workspace, requiring manual maintenance.

4. **Confusing server listings**: When Claude lists running servers, it can't tell which workspace started which server, leading to accidental kills of other workspaces' servers.

## Solution

### 1. Environment-based Port Configuration

Ports are configured via `.env.local` (gitignored) instead of CLAUDE.md instructions:

```bash
# .env.local in ai-safety-course-platform-ws2
API_PORT=8001
VITE_PORT=5174
```

`main.py` reads these as defaults:
- `API_PORT` defaults to 8000 if not set
- `VITE_PORT` defaults to 5173 if not set

When ports aren't configured, `main.py` prints a note:
```
Note: Ports not fully configured in .env.local
  API_PORT not set, using default: 8000
  VITE_PORT not set, using default: 5173
```

### 2. Workspace Identification

`main.py` sets a `WORKSPACE` environment variable from the current directory name when starting. This propagates to child processes (including Vite).

```python
workspace_name = Path.cwd().name
os.environ["WORKSPACE"] = workspace_name
```

### 3. Server Listing Script

A new script `./scripts/list-servers` shows running dev servers with workspace info:

```
PORT   PID    WORKSPACE
8000   12345  ai-safety-course-platform
8001   12346  ai-safety-course-platform-ws2
5173   12347  ai-safety-course-platform (vite)
5174   12348  ai-safety-course-platform-ws2 (vite)
```

The script:
1. Reads server info from `/tmp/dev-servers/*.json` (written by main.py at startup)
2. Cleans up stale entries for dead processes
3. Formats as a table

Note: We use temp files instead of `/proc/<pid>/environ` because `os.environ` changes in Python don't update `/proc/<pid>/environ` (which contains the environment at process start time).

### 4. CLAUDE.md Instructions

Add server management instructions to `CLAUDE.md`:

```markdown
## Dev Server Management

**Starting the server:**
\`\`\`bash
python main.py --dev
\`\`\`
Ports are configured via `.env.local` (API_PORT, VITE_PORT). No need to specify ports on command line.

**Before killing any server, always list first:**
\`\`\`bash
./scripts/list-servers
\`\`\`
This shows which workspace started each server. Only kill servers from YOUR workspace.

**Killing a server by port:**
\`\`\`bash
lsof -ti:<PORT> | xargs kill
\`\`\`
Example: `lsof -ti:8000 | xargs kill` kills only the server on port 8000.

**Never use:** `pkill -f "python main.py"` - this kills ALL dev servers across all workspaces.
```

Remove the "Default Ports by Workspace" section from `~/.claude/ai-safety-course-local.md`.

## Changes Required

### `main.py`

1. Read `API_PORT` and `VITE_PORT` from environment as defaults for CLI args
2. Set `WORKSPACE` environment variable from directory name at startup
3. Print note when using default ports
4. Write server info to `/tmp/dev-servers/<pid>.json` at startup
5. Register atexit handler to clean up the temp file on shutdown
6. Start Vite with `--strictPort` to fail if port is busy (prevents silent escalation to higher ports)

### New file: `scripts/list-servers`

Bash script that lists running dev servers with workspace info.

### `CLAUDE.md`

Add "Dev Server Management" section with instructions for listing and killing servers.

### `~/.claude/ai-safety-course-local.md`

Remove "Default Ports by Workspace" section.

## Impact on Other Developers

- **No action required**: Developers who clone the repo get sensible defaults (8000/5173)
- **Optional**: Can add `.env.local` to customize ports if running multiple workspaces
- **Backwards compatible**: Existing `--port` and `--vite-port` CLI args still work for manual overrides
