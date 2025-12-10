import os
from dotenv import load_dotenv

# Application configuration
LOG_DIR = os.path.join(os.path.expanduser('~'), '.azor')
OUTPUT_DIR = os.path.join(os.path.expanduser('~'), '.azor', 'output')
WAL_FILE = os.path.join(LOG_DIR, 'azor-wal.json')

os.makedirs(LOG_DIR, exist_ok=True)
load_dotenv()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_mcp_server_path() -> str:
    """Returns the path to the MCP server executable."""
    # Default path provided by the user
    default_path = "C:/Users/igorr/Code/azor-session-files-mcp/dist/mcp-server.js"
    return os.getenv('MCP_SERVER_PATH', default_path)