import atexit
import files.config as config
import cli.args
from session import get_session_manager
import command_handler
from cli import console
from cli.prompt import get_user_input
from commands.welcome import print_welcome
from mcp_handler import MCPHandler # Import MCPHandler

def protobuf_to_dict(obj):
    """
    Recursively converts protobuf objects to native Python types.
    Handles MapComposite, RepeatedComposite, and other protobuf types.
    """
    from google.protobuf.internal.containers import MessageMap, ScalarMap, RepeatedCompositeFieldContainer, RepeatedScalarFieldContainer
    from google.protobuf.struct_pb2 import ListValue, Struct, Value
    
    if isinstance(obj, dict):
        return {k: protobuf_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (MessageMap, ScalarMap)):
        # MapComposite - convert to dict and recurse
        return {k: protobuf_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, RepeatedCompositeFieldContainer, RepeatedScalarFieldContainer)):
        # RepeatedComposite - convert to list and recurse
        return [protobuf_to_dict(item) for item in obj]
    elif isinstance(obj, (ListValue, Struct)):
        # Protobuf special types
        return protobuf_to_dict(dict(obj))
    elif isinstance(obj, Value):
        # Protobuf Value wrapper
        return protobuf_to_dict(obj.WhichOneof('kind'))
    elif isinstance(obj, (str, int, float, bool, type(None))):
        # Primitive types
        return obj
    else:
        # Try to convert to dict if it has items() method
        if hasattr(obj, 'items'):
            return {k: protobuf_to_dict(v) for k, v in obj.items()}
        # Try to convert to string as fallback
        return str(obj)

def sanitize_tool_arguments(args: dict) -> dict:
    """
    Sanitizes tool arguments to ensure proper types.
    Detects and fixes string representations of arrays or objects.
    
    Args:
        args: Dictionary of tool arguments
        
    Returns:
        Sanitized dictionary with proper types
    """
    import ast
    import json
    
    sanitized = {}
    for key, value in args.items():
        if isinstance(value, str):
            # Check if it looks like a string representation of a list or dict
            if (value.startswith('[') and value.endswith(']')) or \
               (value.startswith('{') and value.endswith('}')):
                try:
                    # Try to safely evaluate it as a Python literal
                    sanitized[key] = ast.literal_eval(value)
                    console.print_info(f"Converted string '{key}' to proper type: {type(sanitized[key]).__name__}")
                except (ValueError, SyntaxError):
                    try:
                        # Try JSON parsing as fallback
                        sanitized[key] = json.loads(value)
                        console.print_info(f"Converted JSON string '{key}' to proper type: {type(sanitized[key]).__name__}")
                    except json.JSONDecodeError:
                        # If both fail, keep as string
                        sanitized[key] = value
            else:
                sanitized[key] = value
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_tool_arguments(value)
        elif isinstance(value, list):
            # Recursively sanitize list items if they're dicts
            sanitized[key] = [sanitize_tool_arguments(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

def init_chat():
    """Initializes a new session or loads an existing one."""
    print_welcome()

    # Initialize MCPHandler
    mcp_server_path = config.get_mcp_server_path() # Assuming config has this path
    mcp_handler = MCPHandler(mcp_server_path)
    mcp_handler.start() # Start the MCP server
    atexit.register(mcp_handler.shutdown) # Register cleanup for MCP server

    manager = get_session_manager(mcp_handler=mcp_handler)
    
    # Initialize session based on CLI args
    cli_session_id = cli.args.get_session_id_from_cli()
    session = manager.initialize_from_cli(cli_session_id)
    
    # Register cleanup handler
    atexit.register(lambda: manager.cleanup_and_save())

def main_loop():
    """Main loop of the interactive chat."""
    manager = get_session_manager()

    while True:
        try:
            user_input = get_user_input()

            if not user_input:
                continue

            if user_input.startswith('/'):
                should_exit = command_handler.handle_command(user_input)
                if should_exit:
                    break 
                continue
            
            # Conversation with the model
            session = manager.get_current_session()
            
            # Send message (handles WAL logging internally)
            response = session.send_message(user_input)
            
            # Get token information
            total_tokens, remaining_tokens, max_tokens = session.get_token_info()

            # Handle potential tool calls
            if response.parts:
                for part in response.parts:
                    if part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        
                        # Convert Protobuf Struct to Python dict
                        # Use helper function to recursively convert all protobuf types
                        function_args = protobuf_to_dict(function_call.args)
                        
                        # Sanitize arguments to fix any string representations of arrays/objects
                        function_args = sanitize_tool_arguments(function_args)
                        
                        console.print_info(f"Uruchamiam narzędzie: {function_name} z argumentami: {function_args}")
                        
                        # Execute the tool and get the result
                        mcp_handler = manager._mcp_handler # Access the mcp_handler from the session manager
                        if mcp_handler:
                            try:
                                tool_response = mcp_handler.call_tool(function_name, function_args)
                                console.print_tool_output(f"Wynik narzędzia '{function_name}': {tool_response}")
                            except Exception as e:
                                tool_response = {"error": str(e)}
                                console.print_error(f"Błąd podczas wywoływania narzędzia '{function_name}': {e}")
                            
                            # Send the tool response back to the model
                            response = session.send_tool_response(function_name, tool_response)
                            
                            # After a tool call, we expect another model turn, so we continue the loop
                            # and process the new response from the model
                            continue 

            # Display response
            console.print_assistant(f"\n{session.assistant_name}: {response.text}")
            console.print_info(f"Tokens: {total_tokens} (Pozostało: {remaining_tokens} / {max_tokens})")

            # Save session
            success, error = session.save_to_file()
            if not success and error:
                console.print_error(f"Error saving session: {error}")

        except KeyboardInterrupt:
            console.print_info("\nPrzerwano przez użytkownika (Ctrl+C). Uruchamianie procedury finalnego zapisu...")
            break
        except EOFError:
            console.print_info("\nWyjście (Ctrl+D).")
            break
        except Exception as e:
            console.print_error(f"\nWystąpił nieoczekiwany błąd: {e}")
            import traceback
            traceback.print_exc()
            break
