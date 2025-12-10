import subprocess
import atexit
import json
import os
import sys
import threading
from typing import List, Dict, Any, Optional
import uuid # Import uuid for generating unique command IDs
from concurrent.futures import Future # For handling async responses

class MCPHandler:
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self._output_thread: Optional[threading.Thread] = None
        self._error_thread: Optional[threading.Thread] = None # New attribute for stderr thread
        self._lock = threading.Lock()
        self.capabilities: Optional[Dict[str, Any]] = None
        self._pending_commands: Dict[str, Future] = {}
        self._initialization_future: Future = Future() # Initialize a Future for tracking initialization
        self._init_command_id: Optional[str] = None # Store the ID of the initialization command
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
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            print(f"MCP server started at {self.server_path}")

            self._output_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self._output_thread.start()

            self._error_thread = threading.Thread(target=self._read_stderr, daemon=True)
            self._error_thread.start()

            init_id = str(uuid.uuid4())
            self._init_command_id = init_id # Store the init command ID
            # Store the initialization future so we can wait on it later if needed.
            # The result itself will be set in _handle_server_message when the response is received.
            self._pending_commands[init_id] = self._initialization_future 
            self._send_command({"id": init_id, "method": "initialize", "params": {}})
            
            # Do not block here for init_future.result(). The capabilities will be set asynchronously
            # when the response for the 'initialize' command is received by _handle_server_message.
            # The methods that depend on capabilities (like list_tools) will check if it's ready.
            
        except FileNotFoundError:
            print(f"Error: Node.js or the MCP server script not found at {self.server_path}. Ensure Node.js is installed and in your PATH.")
            self.process = None
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            self.process = None

    def _read_stdout(self):
        """Reads output from the subprocess stdout in a separate thread."""
        while self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline()
                if line:
                    self._handle_server_message(line.strip())
                else:
                    break # EOF
            except ValueError:
                break # Process exited

    def _read_stderr(self):
        """Reads output from the subprocess stderr in a separate thread."""
        while self.process and self.process.stderr:
            try:
                line = self.process.stderr.readline()
                if line:
                    sys.stderr.write(f"[MCP STDERR] {line}") # Print to console's stderr
                    sys.stderr.flush()
                else:
                    break # EOF
            except ValueError:
                break # Process exited

    def _handle_server_message(self, message: str, init_id: Optional[str] = None):
        """Processes messages received from the MCP server."""
        try:
            msg = json.loads(message)
            msg_id = msg.get("id")
            if msg_id and msg_id in self._pending_commands:
                future = self._pending_commands.pop(msg_id)
                if "result" in msg:
                    future.set_result(msg["result"])
                    # If this was the initialization message and the future is not yet done,
                    # set capabilities and signal completion.
                    if msg_id == self._init_command_id and not self._initialization_future.done():
                        self.capabilities = msg["result"]
                        self._initialization_future.set_result(True)
                elif "error" in msg:
                    future.set_exception(Exception(msg["error"]))
                else:
                    future.set_exception(Exception(f"Unknown response format: {msg}"))
            elif "error" in msg:
                print(f"MCP Server Error: {msg["error"]}")
            else:
                print(f"MCP Server JSON Output: {msg}") # Print all JSON messages for debugging
        except json.JSONDecodeError:
            print(f"MCP Server Raw Output: {message}") # Print all raw output for debugging

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

    def wait_for_initialization(self, timeout: Optional[float] = 30):
        """Waits for the MCP server to complete its initialization process."""
        try:
            self._initialization_future.result(timeout=timeout)
            return True
        except Exception as e:
            print(f"MCP server initialization timed out or failed: {e}")
            return False

    def shutdown(self):
        """Shuts down the MCP server subprocess."""
        if self.process:
            print("Stopping MCP server...")
            self.process.terminate()
            self.process.wait(timeout=5)  # Give it some time to terminate
            if self.process.poll() is None:
                self.process.kill()
            self.process = None
            print("MCP server stopped.")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists available tools from the MCP server."""
        if not self.process:
            print("MCP server not running, cannot list tools.")
            return []
        
        # Ensure the server is initialized before trying to list tools
        if not self.wait_for_initialization():
            print("MCP server not initialized, cannot list tools.")
            return []

        list_tools_id = str(uuid.uuid4())
        list_tools_future = Future()
        self._pending_commands[list_tools_id] = list_tools_future
        self._send_command({"id": list_tools_id, "method": "list_tools", "params": {}})
        
        try:
            tools = list_tools_future.result(timeout=10) # Adjust timeout as needed
            return tools
        except Exception as e:
            print(f"Error listing tools from MCP server: {e}")
            return []

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calls a tool on the MCP server with the given name and arguments."""
        if not self.capabilities:
            return {"error": "MCP server not initialized, cannot call tool."}
        if not self.process:
            return {"error": "MCP server not running, cannot call tool."}

        call_tool_id = str(uuid.uuid4())
        call_tool_future = Future()
        self._pending_commands[call_tool_id] = call_tool_future
        self._send_command({
            "id": call_tool_id,
            "method": "call_tool",
            "params": {
                "name": name,
                "arguments": arguments
            }
        })
        
        try:
            result = call_tool_future.result(timeout=30) # Adjust timeout as needed
            return result
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

    # Keep the main thread alive for a bit to allow the server to start and print output
    try:
        import time
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        handler.shutdown()
