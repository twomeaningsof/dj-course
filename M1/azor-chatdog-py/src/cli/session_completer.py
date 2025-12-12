from prompt_toolkit.completion import Completer, Completion

class SessionCompleter(Completer):
    """Dynamic completer that fetches session IDs on-the-fly."""
    
    def get_completions(self, document, complete_event):
        # Import here to avoid circular imports
        from files import session_files
        
        # Get current word being typed
        word = document.get_word_before_cursor()
        
        # Fetch sessions dynamically
        sessions = session_files.list_sessions()
        
        # Extract just the IDs
        session_ids = [s['id'] for s in sessions if not s.get('error')]
        
        # Yield matching completions
        for session_id in session_ids:
            if session_id.startswith(word):
                yield Completion(session_id, start_position=-len(word))