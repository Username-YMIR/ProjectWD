# ProjectWD Unreal MCP

This project includes a small local MCP server that connects Codex to Unreal Editor through Unreal's Python Remote Execution feature.

## Codex config

Add this block to `C:\Users\gj\.codex\config.toml`, then restart Codex Desktop.

```toml
[mcp_servers.projectwd_unreal]
command = 'C:\Users\gj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
args = [
  'C:\Users\gj\Documents\Unreal Projects\ProjectWD\Tools\UnrealMCP\unreal_mcp_server.py',
  '--project-root',
  'C:\Users\gj\Documents\Unreal Projects\ProjectWD'
]
startup_timeout_sec = 10
```

## Unreal Editor setup

1. Open `ProjectWD.uproject`.
2. Confirm these plugins are enabled:
   - Python Editor Script Plugin
   - Editor Scripting Utilities
3. In `Edit > Project Settings > Plugins > Python`, confirm `Enable Remote Execution?` is enabled.
4. Restart Unreal Editor after changing plugin or Python settings.

## MCP tools

- `unreal_list_nodes`: discovers running Unreal Editor instances.
- `unreal_python_exec`: executes Python code in the editor.
- `unreal_python_eval`: evaluates a single Python expression in the editor.

## Smoke test

After restarting Codex and opening Unreal Editor, ask Codex:

```text
List Unreal MCP nodes.
```

If no node is found, check that the editor is open and Python Remote Execution is enabled.
