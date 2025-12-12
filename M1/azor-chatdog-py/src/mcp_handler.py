import subprocess
import atexit
import json
import os
import sys
import threading
from typing import List, Dict, Any, Optional
import uuid

class MCPHandler:
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self.capabilities: Optional[Dict[str, Any]] = None
        atexit.register(self.shutdown)

    def start(self):
        """Starts the MCP server as a subprocess and establishes communication."""
        if self.process:
            print("MCP server is already running.")
            return

        try:
            command_list = ['node', self.server_path]
            print(f"Attempting to start MCP server with command: {' '.join(command_list)}")
            self.process = subprocess.Popen(
                command_list,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            print(f"MCP server started at {self.server_path}")

            # Initialize synchronous handshake
            init_id = str(uuid.uuid4())
            self._send_command({
                "id": init_id, 
                "method": "initialize", 
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "azor-chatdog-py", "version": "1.0.0"}
                }
            })
            
            # Read init response immediately
            resp = self.process.stdout.readline()
            if not resp:
                raise Exception("MCP server closed stream during initialization")
            
            msg = json.loads(resp.strip())
            if "result" in msg and "capabilities" in msg["result"]:
                self.capabilities = msg["result"]["capabilities"]
                print(f"DEBUG: Capabilities received: {self.capabilities}")
            else:
                 print(f"DEBUG: Init response unexpected: {msg}")

            # Send initialized notification
            self._send_command({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            })
            
        except FileNotFoundError:
            print(f"Error: Node.js or the MCP server script not found at {self.server_path}.")
            self.process = None
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            self.process = None

    def _send_command(self, command: Dict[str, Any]) -> None:
        """Sends a command to the MCP server's stdin."""
        if not self.process or not self.process.stdin:
            print("MCP server not running, cannot send command.")
            return

        with self._lock:
            try:
                command_str = json.dumps(command) + '\n'
                self.process.stdin.write(command_str)
                self.process.stdin.flush()
            except Exception as e:
                print(f"Error sending command to MCP server: {e}")

    def wait_for_initialization(self, timeout: Optional[float] = 30) -> Optional[Dict[str, Any]]:
        """
        Returns capabilities safely. Since initialization is now synchronous in start(),
        this just checks if initialization succeeded.
        """
        if self.capabilities:
            return self.capabilities
        return None

    def shutdown(self):
        """Shuts down the MCP server subprocess."""
        if self.process:
            print("Stopping MCP server...")
            self.process.terminate()
            self.process.wait(timeout=5)
            if self.process.poll() is None:
                self.process.kill()
            self.process = None
            print("MCP server stopped.")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lists available tools from the MCP server.
        """
        if not self.capabilities or not self.process:
            print("MCP server not initialized or not running, cannot list tools.")
            return []

        return self.capabilities.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a tool on the MCP server with the given name and arguments.
        """
        if not self.capabilities:
            return {"error": "MCP server not initialized, cannot call tool."}
        if not self.process:
            return {"error": "MCP server not running, cannot call tool."}

        call_tool_id = str(uuid.uuid4())
        
        # Send command
        self._send_command({
            "jsonrpc": "2.0",
            "id": call_tool_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        })
        
        # Read response loop
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    return {"error": "MCP server closed stream"}
                
                try:
                    msg = json.loads(line.strip())
                    if msg.get("id") == call_tool_id:
                        if "result" in msg:
                            return msg["result"]
                        elif "error" in msg:
                            return {"error": msg["error"]}
                    # Ignore notifications/other messages for now
                    # In a real async client, we would handle them.
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error calling tool '{name}' on MCP server: {e}")
            return {"error": str(e)}

if __name__ == '__main__':
    # Example usage (for testing purposes)
    MCP_SERVER_PATH = "C:/Users/igorr/Code/azor-session-files-mcp/dist/mcp-server.js"
    handler = MCPHandler(MCP_SERVER_PATH)
    handler.start()
    
    if handler.capabilities:
        tools = handler.list_tools()
        print(f"Available Tools: {tools}")

    try:
        import time
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        handler.shutdown()
