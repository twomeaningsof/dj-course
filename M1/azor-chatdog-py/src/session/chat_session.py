import uuid
from typing import List, Any, Optional, Union
import os
from files import session_files
from files.wal import append_to_wal
from llm.gemini_client import GeminiLLMClient
from llm.llama_client import LlamaClient
from assistant import Assistant
from cli import console

# Context token limit

# Engine to Client Class mapping
ENGINE_MAPPING = {
    'LLAMA_CPP': LlamaClient,
    'GEMINI': GeminiLLMClient,
}


class ChatSession:
    """
    Manages everything related to a single chat session.
    Encapsulates session ID, conversation history, assistant, LLM chat session, and session title.
    """
    
    DEFAULT_TITLE = "New Session"

    def __init__(self, assistant: Assistant, session_id: str | None = None, history: List[Any] | None = None, title: str | None = None):
        """
        Initialize a chat session.
        
        Args:
            assistant: Assistant instance that defines the behavior and model for this session
            session_id: Unique session identifier. If None, generates a new UUID.
            history: Initial conversation history. If None, starts empty.
            title: Human-readable title of the session.
        """
        self.assistant = assistant
        self.session_id = session_id or str(uuid.uuid4())
        self._history = history or []
        self.title = title or self.DEFAULT_TITLE
        self._llm_client: Union[GeminiLLMClient, LlamaClient, None] = None
        self._llm_chat_session = None
        self._max_context_tokens = 32768
        self._initialize_llm_session()
    
    def _initialize_llm_session(self):
        """
        Creates or recreates the LLM chat session with current history.
        This should be called after any history modification.
        """
        # Walidacja zmiennej ENGINE
        engine = os.getenv('ENGINE', 'GEMINI').upper()
        if engine not in ENGINE_MAPPING:
            valid_engines = ', '.join(ENGINE_MAPPING.keys())
            raise ValueError(f"ENGINE musi być jedną z wartości: {valid_engines}, otrzymano: {engine}")
        
        # Initialize LLM client if not already created
        if self._llm_client is None:
            SelectedClientClass = ENGINE_MAPPING.get(engine, GeminiLLMClient)
            console.print_info(SelectedClientClass.preparing_for_use_message())
            self._llm_client = SelectedClientClass.from_environment()
            console.print_info(self._llm_client.ready_for_use_message())
        
        self._llm_chat_session = self._llm_client.create_chat_session(
            system_instruction=self.assistant.system_prompt,
            history=self._history,
            thinking_budget=0
        )
    
    
    @classmethod
    def load_from_file(cls, assistant: Assistant, session_id: str) -> tuple['ChatSession | None', str | None]:
        """
        Loads a session from disk.
        
        Args:
            assistant: Assistant instance to use for this session
            session_id: ID of the session to load
            
        Returns:
            tuple: (ChatSession object or None, error_message or None)
        """
     
        try:
            result = session_files.load_session_history(session_id)
            
            # Handle backward compatibility if load_session_history returns 2 values
            if len(result) == 2:
                history, error = result
                title = None
            else:
                history, title, error = result

            if error:
                return None, error
            
            session = cls(assistant=assistant, session_id=session_id, history=history, title=title)
            return session, None
            
        except ValueError as e:
            return None, f"Error unpacking session data: {e}"
    
    def save_to_file(self) -> tuple[bool, str | None]:
        """
        Saves this session to disk including the title.
        Only saves if history has at least one complete exchange.
        
        Returns:
            tuple: (success: bool, error_message: str | None)
        """
        # Sync history from LLM session before saving
        if self._llm_chat_session:
            self._history = self._llm_chat_session.get_history()
        
        return session_files.save_session_history(
            self.session_id, 
            self._history, 
            self.assistant.system_prompt, 
            self._llm_client.get_model_name(),
            title=self.title  # Added title argument
        )
    
    def rename(self, new_title: str) -> bool:
        """
        Renames the current session and saves the change.
        
        Args:
            new_title: The new title string.
            
        Returns:
            bool: True if save was successful.
        """
        self.title = new_title
        success, _ = self.save_to_file()
        return success

    def send_message(self, text: str) -> Any:
        """
        Sends a message to the LLM and returns the response.
        Updates internal history (synchronizes with LLM chat session) and logs to WAL.
        Auto-generates title by LLM after the first response.
        
        Args:
            text: User's message
            
        Returns:
            Response object from Google GenAI (lub równoważny obiekt z AzorAssistant)
        """
        if not self._llm_chat_session:
            raise RuntimeError("LLM session not initialized")
        
        # 1. Wysłanie wiadomości i odebranie odpowiedzi
        response = self._llm_chat_session.send_message(text)
        
        # 2. Sync history po wiadomości
        self._history = self._llm_chat_session.get_history()
        
        # 3. LOGIKA AUTOMATYCZNEGO TYTUŁOWANIA PRZEZ LLM
        # Jeśli tytuł jest domyślny ORAZ historia ma 2 elementy (pierwsza pełna wymiana)
        if self.title == self.DEFAULT_TITLE and len(self._history) == 2:
            new_title = self._generate_title_from_history()
            if new_title:
                self.title = new_title
                # Utrwal tytuł natychmiast na dysku
                self.save_to_file()
        
        # 4. Log do WAL
        total_tokens = self.count_tokens()
        success, error = append_to_wal(
            session_id=self.session_id,
            prompt=text,
            response_text=response.text,
            total_tokens=total_tokens,
            model_name=self._llm_client.get_model_name()
        )
        
        if not success and error:
            # We don't want to fail the entire message sending because of WAL issues
            pass
        
        return response
    
    def get_history(self) -> List[Any]:
        """Returns the current conversation history."""
        # Always sync from LLM session to ensure consistency
        if self._llm_chat_session:
            self._history = self._llm_chat_session.get_history()
        return self._history
    
    def get_title(self) -> str:
        """Return the current session title."""
        return self.title
    
    def clear_history(self):
        """Clears all conversation history and reinitializes the LLM session."""
        self._history = []
        self._initialize_llm_session()
        self.save_to_file()
    
    def pop_last_exchange(self) -> bool:
        """
        Removes the last user-assistant exchange from history.
        
        Returns:
            bool: True if successful, False if insufficient history
        """
        current_history = self.get_history()
        
        if len(current_history) < 2:
            return False
        
        # Remove last 2 entries (user + assistant)
        self._history = current_history[:-2]
        
        # Reinitialize LLM session with modified history
        self._initialize_llm_session()
        
        self.save_to_file()
        
        return True
    
    def count_tokens(self) -> int:
        """
        Counts total tokens in the conversation history.
        
        Returns:
            int: Total token count
        """
        if not self._llm_client:
            return 0
        return self._llm_client.count_history_tokens(self._history)
    
    def is_empty(self) -> bool:
        """
        Checks if session has any complete exchanges.
        
        Returns:
            bool: True if history has less than 2 entries
        """
        return len(self._history) < 2
    
    def get_remaining_tokens(self) -> int:
        """
        Calculates remaining tokens based on context limit.
        
        Returns:
            int: Remaining token count
        """
        total = self.count_tokens()
        return self._max_context_tokens - total
    
    def get_token_info(self) -> tuple[int, int, int]:
        """
        Gets comprehensive token information for this session.
        
        Returns:
            tuple: (total_tokens, remaining_tokens, max_tokens)
        """
        total_tokens = self.count_tokens()
        remaining_tokens = self._max_context_tokens - total_tokens
        max_tokens = self._max_context_tokens
        return total_tokens, remaining_tokens, max_tokens
    
    def _generate_title_from_history(self) -> Optional[str]:
        """
        Generuje krótki tytuł wątku na podstawie pierwszej wymiany, 
        używając niezależnego zapytania do LLM.
        Tytuł jest jednozdaniowy, bez znaków interpunkcyjnych.
        """
        # Historia musi mieć dokładnie 2 elementy: Wiadomość użytkownika [0] i odpowiedź asystenta [1]
        if len(self._history) != 2:
            return None
        
        # Sprawdzamy, czy klient LLM jest dostępny
        if not self._llm_client:
            return None

        # 1. Ekstrakcja pierwszej wymiany z formatu {"role": "...", "parts": [{"text": "..."}]}
        try:
            # Poprawny dostęp do treści wiadomości przez klucze 'parts' i 'text'
            first_user_message = self._history[0]['parts'][0]['text']
            first_assistant_response = self._history[1]['parts'][0]['text']
        except (KeyError, IndexError):
            # Logowanie lub ignorowanie błędu, jeśli format historii jest nieprawidłowy
            return None
        
        # 2. Konstrukcja promptu do generowania tytułu
        titling_prompt = (
            "Na podstawie poniższego dialogu, wygeneruj krótki, jednozdaniowy tytuł wątku. "
            "Tytuł musi być bez znaków interpunkcyjnych i oparty na treści odpowiedzi asystenta. "
            "Dialog:\n"
            f"UŻYTKOWNIK: {first_user_message}\n"
            f"ASYSTENT: {first_assistant_response}"
        )
        
        try:
            # 3. Wywołanie niezależnej metody LLM
            # Wymagane jest, aby self._llm_client.generate_title_text() zwracał czysty tekst.
            title_response = self._llm_client.generate_title_text(
                prompt=titling_prompt
            )

            # 4. Czyszczenie i formatowanie
            cleaned_title = title_response.strip()
            
            # Usuwanie końcowych znaków interpunkcyjnych (dla bezpieczeństwa, jeśli LLM ich użyje)
            if cleaned_title and cleaned_title[-1] in ('.', '!', '?', ','):
                cleaned_title = cleaned_title[:-1].strip()
            
            # Upewnienie się, że tytuł nie jest pusty
            if not cleaned_title:
                return None
            
            return cleaned_title
            
        except Exception as e:
            # Obsługa wszelkich innych błędów związanych z API lub generowaniem
            # Możesz użyć konsoli do logowania błędu, jeśli jest importowana
            # console.print_error(f"Ostrzeżenie: Nie udało się wygenerować automatycznego tytułu: {e}")
            return None
    
    @property
    def assistant_name(self) -> str:
        """
        Gets the display name of the assistant.
        
        Returns:
            str: The assistant's display name
        """
        return self.assistant.name