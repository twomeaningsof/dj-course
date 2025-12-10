import atexit
import files.config as config
import cli.args
from session import get_session_manager
import command_handler
from cli import console
from cli.prompt import get_user_input
from commands.welcome import print_welcome
from mcp_handler import MCPHandler # Import MCPHandler

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
                        function_args = {k: v for k, v in function_call.args.items()}
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
