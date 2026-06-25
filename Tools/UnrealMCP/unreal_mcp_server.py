#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from pathlib import Path


SERVER_NAME = "projectwd-unreal"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"
EXEC_MODES = {
    "file": "ExecuteFile",
    "statement": "ExecuteStatement",
    "eval": "EvaluateStatement",
    "ExecuteFile": "ExecuteFile",
    "ExecuteStatement": "ExecuteStatement",
    "EvaluateStatement": "EvaluateStatement",
}


class McpError(Exception):
    def __init__(self, message, code=-32000):
        super().__init__(message)
        self.code = code


def log(message):
    print(message, file=sys.stderr, flush=True)


def send_message(message):
    payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(b"Content-Length: " + str(len(payload)).encode("ascii") + b"\r\n\r\n")
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def read_message():
    line = sys.stdin.buffer.readline()
    if not line:
        return None

    if line.lower().startswith(b"content-length:"):
        content_length = int(line.split(b":", 1)[1].strip())
        while True:
            header = sys.stdin.buffer.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        payload = sys.stdin.buffer.read(content_length)
        return json.loads(payload.decode("utf-8"))

    if not line.strip():
        return read_message()

    return json.loads(line.decode("utf-8"))


def response(request_id, result):
    send_message({"jsonrpc": "2.0", "id": request_id, "result": result})


def error_response(request_id, code, message):
    send_message({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def find_engine_python_path(project_root):
    configured = os.environ.get("UE_PYTHON_REMOTE_EXECUTION")
    if configured:
        return Path(configured)

    uproject_files = list(project_root.glob("*.uproject"))
    engine_association = "5.8"
    if uproject_files:
        with uproject_files[0].open("r", encoding="utf-8") as handle:
            engine_association = json.load(handle).get("EngineAssociation", engine_association)

    return Path(
        "C:/Program Files/Epic Games"
    ) / f"UE_{engine_association}" / "Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py"


def load_remote_execution(project_root):
    remote_execution_path = find_engine_python_path(project_root)
    if not remote_execution_path.exists():
        raise McpError(f"Unreal remote_execution.py not found: {remote_execution_path}")

    sys.path.insert(0, str(remote_execution_path.parent))
    import remote_execution

    return remote_execution


def discover_nodes(remote_execution, timeout_seconds):
    session = remote_execution.RemoteExecution()
    session.start()
    try:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            nodes = session.remote_nodes
            if nodes:
                return nodes
            time.sleep(0.1)
        return []
    finally:
        session.stop()


def run_unreal_python(remote_execution, code, mode, node_id, timeout_seconds):
    session = remote_execution.RemoteExecution()
    session.start()
    try:
        deadline = time.time() + timeout_seconds
        nodes = []
        while time.time() < deadline:
            nodes = session.remote_nodes
            if nodes:
                break
            time.sleep(0.1)

        if not nodes:
            raise McpError("No Unreal Editor Python remote execution node found.")

        target_node = None
        if node_id:
            target_node = next((node for node in nodes if node.get("node_id") == node_id), None)
            if not target_node:
                raise McpError(f"Unreal node not found: {node_id}")
        else:
            target_node = nodes[0]

        session.open_command_connection(target_node["node_id"])
        result = session.run_command(code, unattended=True, exec_mode=mode, raise_on_failure=False)
        return {"node": target_node, "result": result}
    finally:
        session.stop()


def tool_definitions():
    return [
        {
            "name": "unreal_list_nodes",
            "description": "Discover running Unreal Editor instances with Python Remote Execution enabled.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "timeout_seconds": {
                        "type": "number",
                        "description": "How long to wait for Unreal Editor discovery.",
                        "default": 5,
                    }
                },
            },
        },
        {
            "name": "unreal_python_exec",
            "description": "Execute Python code in the running Unreal Editor through Python Remote Execution.",
            "inputSchema": {
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute in Unreal Editor."},
                    "mode": {
                        "type": "string",
                        "enum": ["file", "statement", "eval", "ExecuteFile", "ExecuteStatement", "EvaluateStatement"],
                        "default": "file",
                    },
                    "node_id": {"type": "string", "description": "Optional Unreal node id from unreal_list_nodes."},
                    "timeout_seconds": {"type": "number", "default": 8},
                },
            },
        },
        {
            "name": "unreal_python_eval",
            "description": "Evaluate a single Python expression in the running Unreal Editor.",
            "inputSchema": {
                "type": "object",
                "required": ["expression"],
                "properties": {
                    "expression": {"type": "string", "description": "Python expression to evaluate in Unreal Editor."},
                    "node_id": {"type": "string", "description": "Optional Unreal node id from unreal_list_nodes."},
                    "timeout_seconds": {"type": "number", "default": 8},
                },
            },
        },
    ]


def text_result(value):
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, indent=2, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}]}


def handle_tool_call(name, arguments, remote_execution):
    arguments = arguments or {}
    timeout_seconds = float(arguments.get("timeout_seconds", 5))

    if name == "unreal_list_nodes":
        return text_result(discover_nodes(remote_execution, timeout_seconds))

    if name == "unreal_python_exec":
        mode = EXEC_MODES.get(arguments.get("mode", "file"))
        if not mode:
            raise McpError(f"Unsupported execution mode: {arguments.get('mode')}")
        return text_result(
            run_unreal_python(
                remote_execution,
                arguments["code"],
                mode,
                arguments.get("node_id"),
                timeout_seconds,
            )
        )

    if name == "unreal_python_eval":
        return text_result(
            run_unreal_python(
                remote_execution,
                arguments["expression"],
                "EvaluateStatement",
                arguments.get("node_id"),
                timeout_seconds,
            )
        )

    raise McpError(f"Unknown tool: {name}", code=-32601)


def handle_request(message, remote_execution):
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    try:
        if method == "initialize":
            protocol_version = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
            response(
                request_id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        elif method == "tools/list":
            response(request_id, {"tools": tool_definitions()})
        elif method == "tools/call":
            response(request_id, handle_tool_call(params.get("name"), params.get("arguments"), remote_execution))
        elif method in ("ping",):
            response(request_id, {})
        else:
            raise McpError(f"Unsupported method: {method}", code=-32601)
    except McpError as exc:
        error_response(request_id, exc.code, str(exc))
    except Exception as exc:
        error_response(request_id, -32000, str(exc))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    remote_execution = load_remote_execution(project_root)
    log(f"{SERVER_NAME} MCP server started for {project_root}")

    while True:
        message = read_message()
        if message is None:
            break
        if "id" in message:
            handle_request(message, remote_execution)


if __name__ == "__main__":
    main()
