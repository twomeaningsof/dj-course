from cli import console
from .chat_session import ChatSession
from assistant import create_azor_assistant, create_perfectionist_assistant, create_empathetic_assistant, create_angel_investor_assistant, create_sparing_partner_assistant
from files import session_files
from typing import List, Dict, Any, Optional 


class SessionManager:
    """
    Orchestrates session lifecycle and manages the current active session.
    Provides high-level operations for session management.
    """
    
    _ASSISTANT_FACTORY = {
        'AZOR': create_azor_assistant,
        'PERFECTIONIST': create_perfectionist_assistant,
        'EMPATHETIC': create_empathetic_assistant,
        'ANGEL': create_angel_investor_assistant,
        'SPARING': create_sparing_partner_assistant,
    }

    @classmethod
    def get_available_assistant_types(cls) -> List[str]:
        """Returns a list of available assistant types."""
        return list(cls._ASSISTANT_FACTORY.keys())
    
    def __init__(self, mcp_handler: Optional[Any] = None):
        """Initializes with no active session."""
        self._current_session: ChatSession | None = None
        self._mcp_handler = mcp_handler
    
    def _get_assistant_creator(self, assistant_type: str):
        """
        Zwraca funkcję tworzącą asystenta na podstawie typu (domyślnie azor).
        """
        return self._ASSISTANT_FACTORY.get(assistant_type, create_azor_assistant)
    
    def get_current_session(self) -> ChatSession:
        """
        Returns the current active session.
        
        Raises:
            RuntimeError: If no session is active
        """
        if not self._current_session:
            raise RuntimeError("No active session. Call create_new_session() or switch_to_session() first.")
        return self._current_session
    
    def has_active_session(self) -> bool:
        """Returns True if there's an active session."""
        return self._current_session is not None
    
    def create_new_session(self, save_current: bool = True, assistant_type: str = 'azor') -> tuple[ChatSession, bool, str | None, str | None]:
        """
        Creates a new session, optionally saving the current one.
        
        Args:
            save_current: If True, saves current session before creating new one
            
        Returns:
            tuple: (new_session, save_attempted, previous_session_id, save_error)
                - new_session: The newly created session
                - save_attempted: Whether saving was attempted
                - previous_session_id: ID of the previous session (if any)
                - save_error: Error message if save failed, None if successful
        """
        save_attempted = False
        previous_session_id = None
        save_error = None
        
        # Save current session if requested
        if save_current and self._current_session:
            save_attempted = True
            previous_session_id = self._current_session.session_id
            success, error = self._current_session.save_to_file()
            if not success:
                save_error = error
        
        # Create new session
        create_assistant_func = self._get_assistant_creator(assistant_type)
            
        try:
            assistant = create_assistant_func()
        except Exception as e:
            print(f"Błąd podczas tworzenia asystenta typu '{assistant_type}': {e}")
            # Dla uproszczenia, w razie błędu wracamy do domyślnego 'azor'
            assistant = create_azor_assistant()
    
        new_session = ChatSession(assistant=assistant, mcp_handler=self._mcp_handler)
        self._current_session = new_session
    
        return new_session, save_attempted, previous_session_id, save_error
    
    def switch_to_session(self, session_id: str) -> tuple[ChatSession | None, bool, str | None, bool, str | None, bool]:
        """
        Switches to an existing session by ID.
        Saves current session before switching.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            tuple: (new_session, save_attempted, previous_session_id, load_successful, load_error, has_history)
                - new_session: The loaded session (None if failed)
                - save_attempted: Whether saving previous session was attempted
                - previous_session_id: ID of the previous session (if any)
                - load_successful: Whether loading was successful
                - load_error: Error message if load failed, None if successful
                - has_history: Whether the loaded session has history (only valid if load_successful)
        """
        save_attempted = False
        previous_session_id = None
        
        # Save current session
        if self._current_session:
            save_attempted = True
            previous_session_id = self._current_session.session_id
            self._current_session.save_to_file()
        
        # Load new session
        assistant = create_azor_assistant()
        new_session, error = ChatSession.load_from_file(session_id=session_id, mcp_handler=self._mcp_handler)
        
        if error:
            # Failed to load - don't change current session
            return None, save_attempted, previous_session_id, False, error, False
        
        # Successfully loaded - update current session
        self._current_session = new_session
        has_history = not new_session.is_empty()
        
        return new_session, save_attempted, previous_session_id, True, None, has_history

    def remove_current_session_and_create_new(self) -> tuple[ChatSession, str, bool, str | None]:
        """
        Removes the current session file and immediately creates a new, empty session.

        Returns:
            A tuple containing the new session, the ID of the removed session, 
            a boolean indicating if the removal was successful, and an optional error message.
        """
        if not self._current_session:
            raise RuntimeError("No session is active to remove.")

        removed_session_id = self._current_session.session_id
        
        # Remove the session file
        remove_success, remove_error = session_files.remove_session_file(removed_session_id)

        # Create a new session regardless of whether the file was successfully removed
        assistant = create_azor_assistant()
        new_session = ChatSession(assistant=assistant, mcp_handler=self._mcp_handler)
        self._current_session = new_session

        return new_session, removed_session_id, remove_success, remove_error

    def initialize_from_cli(self, cli_session_id: str | None) -> ChatSession:
        """
        Initializes a session based on CLI arguments.
        Either loads an existing session or creates a new one.
        
        Args:
            cli_session_id: Session ID from CLI, or None for new session
            
        Returns:
            ChatSession: The initialized session
        """
        # POPRAWKA: Przeniesienie definicji na początek funkcji
        assistant = create_azor_assistant()

        if cli_session_id :
            # Usunięto powtórzoną definicję assistant = create_azor_assistant()
            session, error = ChatSession.load_from_file(session_id=cli_session_id, mcp_handler=self._mcp_handler)
            
            if error:
                console.print_error(error)
                # Fallback to new session
                session = ChatSession(assistant=assistant, mcp_handler=self._mcp_handler)
                console.print_info(f"Rozpoczęto nową sesję. ID: {session.session_id}")
            else:
                # DODANO: Wyświetlenie tytułu przy ładowaniu
                console.print_info(f"Wczytano sesję '{session.title}'. ID: {session.session_id}")
                
            self._current_session = session
            
            console.display_help(session.session_id)
            if not session.is_empty():
                # Import przeniesiony niżej, aby uniknąć cyklicznych zależności
                from commands.session_summary import display_history_summary
                display_history_summary(session.get_history(), session.assistant_name)
        else:
            print("Rozpoczynanie nowej sesji.")
            # Usunięto powtórzoną definicję assistant = create_azor_assistant()
            session = ChatSession(assistant=assistant, mcp_handler=self._mcp_handler)
            self._current_session = session
            # DODANO: Wyświetlenie tytułu nowej sesji
            console.print_info(f"Rozpoczęto nową sesję '{session.title}'. ID: {session.session_id}")
            console.display_help(session.session_id)
        
        return session
    
    def cleanup_and_save(self):
        """
        Cleanup method to be called on program exit.
        Saves the current session if it has content.
        """
        if not self._current_session:
            return
        
        session = self._current_session
        
        if session.is_empty():
            console.print_info(f"\nSesja '{session.title}' jest pusta/niekompletna. Pominięto finalny zapis.")
        else:
            # DODANO: Wyświetlenie tytułu sesji
            console.print_info(f"\nFinalny zapis historii sesji '{session.title}'. ID: {session.session_id}")
            session.save_to_file()
            console.display_final_instructions(session.session_id)

    # NOWA METODA: Do wyświetlania listy wszystkich sesji w CLI
    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all saved sessions including their title and ID.
        
        Returns:
            List[dict]: Lista słowników z danymi sesji.
        """
        return session_files.list_sessions()
    
    def rename_current_session(self, new_title: str) -> tuple[bool, str | None]:
        """
        Zmienia tytuł aktywnej sesji i zapisuje go na dysku.
        
        Args:
            new_title: Nowy tytuł sesji.
            
        Returns:
            tuple: (success: bool, error_message: str | None)
        """
        if not self._current_session:
            return False, "Brak aktywnej sesji. Nie można zmienić tytułu."
        
        session = self._current_session
        
        # Zmiana tytułu przez metodę w ChatSession
        success = session.rename(new_title)
        
        if success:
            return True, None
        else:
            return False, f"Błąd podczas próby zapisu sesji '{session.session_id}' po zmianie tytułu"
        
    def get_current_session_title(self) -> str:
        if not self._current_session:
            return "Brak aktywnej sesji. Nie można zwrócić tytułu."
        
        session = self._current_session
        
        return session.get_title()
    
    def switch_assistant(self, new_assistant_type: str) -> tuple[bool, str | None, str | None]:
        """
        Przełącza asystenta w ramach aktywnej sesji, zachowując historię.
        
        Args:
            new_assistant_type: Typ nowego asystenta (np. 'PERFECTIONIST').
            
        Returns:
            tuple: (success: bool, old_assistant_type: str | None, error_message: str | None)
        """
        if not self._current_session:
            return False, None, "Brak aktywnej sesji. Nie można zmienić asystenta."

        old_assistant_name = self._current_session.assistant.name
        
        # 1. Pobranie funkcji tworzącej asystenta
        create_assistant_func = self._get_assistant_creator(new_assistant_type.upper())
        
        try:
            # 2. Utworzenie nowego asystenta
            new_assistant = create_assistant_func()
            
            # 3. Przypisanie nowego asystenta do aktywnej sesji
            self._current_session.set_assistant(new_assistant)
            
            # 4. Ponowne inicjowanie sesji LLM z nowym asystentem
            # Kluczowe: należy utworzyć nową sesję czatu LLM (np. Gemini ChatSession), 
            # używając historii starej sesji oraz nowej instrukcji systemowej asystenta.
            self._current_session._initialize_llm_session()
            
            self._current_session.save_to_file()
            
            return True, old_assistant_name, None
        
        except Exception as e:
            error_msg = f"Błąd podczas przełączania asystenta na '{new_assistant_type}': {e}"
            return False, old_assistant_name, error_msg