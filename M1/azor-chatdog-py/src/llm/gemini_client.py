"""
Google Gemini LLM Client Implementation
Encapsulates all Google Gemini AI interactions.
"""

import os
import sys
from typing import Optional, List, Any, Dict
import google.generativeai as genai
import google.generativeai.types as genai_types # Keep for other types, but Content/Part are likely elsewhere
import google.ai.generativelanguage as glm # Import generativelanguage module
from google.generativeai.types import FunctionDeclaration, Tool, GenerateContentResponse
from dotenv import load_dotenv
from cli import console
from .gemini_validation import GeminiConfig
from mcp_handler import MCPHandler # Import MCPHandler
from mcp_tool_adapter import mcp_tools_to_gemini_tools # Import tool adapter

class GeminiChatSessionWrapper:
    """
    Wrapper for Gemini chat session that provides universal dictionary-based history format.
    This ensures compatibility with LlamaClient's history format.
    """
    
    def __init__(self, gemini_session, assistant_name: str):
        """
        Initialize wrapper with Gemini chat session.
        
        Args:
            gemini_session: The actual Gemini chat session object
        """
        self.gemini_session = gemini_session
        self.assistant_name = assistant_name
    
    def send_message(self, text: str) -> Any:
        """
        Forwards message to Gemini session.
        
        Args:
            text: User's message
            
        Returns:
            Response object from Gemini
        """
        return self.gemini_session.send_message(text)

    def send_tool_response(self, tool_name: str, tool_response: Dict[str, Any]) -> Any:
        """
        Sends a tool response back to the Gemini session.

        Args:
            tool_name: The name of the tool that was called.
            tool_response: The response from the tool execution.

        Returns:
            Response object from Gemini
        """
        function_response_part = glm.Part(
            function_response=glm.FunctionResponse(
                name=tool_name,
                response=tool_response
            )
        )
        return self.gemini_session.send_message([function_response_part])
    
    def display_clarification_request(self, question: str, reason: str, suggestions: Optional[List[str]] = None) -> None:
        """
        Displays a clarification request to the user.
        This is called when the model uses the request_clarification tool.
        
        Args:
            question: The question to ask the user
            reason: Why clarification is needed
            suggestions: Optional list of suggested answers
        """
        console.print_info(f"\n{'='*60}")
        console.print_info(f"🤔 [{self.assistant_name}] WYMAGA WYJAŚNIENIA")
        console.print_info(f"{'='*60}")
        console.print_info(f"Powód: {reason}")
        console.print_info(f"\nPytanie: {question}")
        
        if suggestions and len(suggestions) > 0:
            console.print_info(f"\nSugerowane opcje:")
            for i, suggestion in enumerate(suggestions, 1):
                console.print_info(f"  {i}. {suggestion}")
        
        console.print_info(f"{'='*60}\n")
    
    def get_history(self) -> List[Dict]:
        """
        Gets conversation history in universal dictionary format.
        
        Returns:
            List of dictionaries with format: {"role": "user|model", "parts": [{"text": "..."}]}
        """
        gemini_history = self.gemini_session.history # Directly access the history attribute
        universal_history = []
        
        for content in gemini_history:
            # Convert Gemini Content object to universal dictionary format
            text_part = ""
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_part = part.text
                        break
            
            if text_part:
                universal_content = {
                    "role": content.role,
                    "parts": [{"text": text_part}]
                }
                    
                universal_history.append(universal_content)
        
        return universal_history

class GeminiLLMClient:
    """
    Encapsulates all Google Gemini AI interactions.
    Provides a clean interface for chat sessions, token counting, and configuration.
    """
    
    def __init__(self, model_name: str, api_key: str, mcp_handler: Optional[MCPHandler] = None):
        """
        Initialize the Gemini LLM client with explicit parameters.
        
        Args:
            model_name: Model to use (e.g., 'gemini-2.5-flash')
            api_key: Google Gemini API key
            mcp_handler: Optional MCPHandler instance to provide tools
        
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key cannot be empty or None")
        
        self.system_instruction = ""
        self.model_name = model_name
        self.api_key = api_key
        self._mcp_handler = mcp_handler
        self._gemini_tools: List[genai.types.Tool] = []

        # Configure the API key globally
        genai.configure(api_key=self.api_key)

        # Build MCP tools if handler is provided
        if self._mcp_handler:
            capabilities = self._mcp_handler.wait_for_initialization()
            if capabilities is None:
                console.print_error("MCP server failed to initialize. No tools will be loaded.")
                self._gemini_tools = []
            else:
                self._gemini_tools = mcp_tools_to_gemini_tools(capabilities.get("tools", []))
                console.print_info(f"Loaded {len(self._gemini_tools)} MCP tools for Gemini.")

        # Create clarification tool and combine with MCP tools
        self._clarification_tool = self._create_clarification_tool()
        all_tools = list(self._gemini_tools)  # Copy MCP tools
        all_tools.append(self._clarification_tool)  # Add clarification tool

        # Initialize the model with all tools
        self._model = genai.GenerativeModel(model_name=self.model_name, tools=all_tools)
    
    def _create_clarification_tool(self) -> genai.types.Tool:
        """
        Creates a Gemini tool for requesting user clarification.
        The model can call this tool when it needs more information from the user.
        
        Returns:
            Tool object with clarification function declaration
        """
        clarification_declaration = FunctionDeclaration(
            name="request_clarification",
            description=(
                "Request clarification from the user when the information "
                "provided is ambiguous, incomplete, or when you need more "
                "details to provide an accurate response. Use this tool "
                "when you're unsure about the user's intent or need "
                "additional context."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The specific question to ask the user for clarification"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why clarification is needed"
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of suggested answers or options for the user"
                    }
                },
                "required": ["question", "reason"]
            }
        )
        
        return Tool(function_declarations=[clarification_declaration])

    @staticmethod
    def preparing_for_use_message() -> str:
        """
        Returns a message indicating that Gemini client is being prepared.
        
        Returns:
            Formatted preparation message string
        """
        return "🤖 Przygotowywanie klienta Gemini..."
    
    @classmethod
    def from_environment(cls, mcp_handler: Optional[MCPHandler] = None) -> 'GeminiLLMClient':
        """
        Factory method that creates a GeminiLLMClient instance from environment variables.
        
        Returns:
            GeminiLLMClient instance initialized with environment variables
            
        Raises:
            ValueError: If required environment variables are not set
        """
        load_dotenv()
    
        # Walidacja z Pydantic
        config = GeminiConfig(
            model_name=os.getenv('MODEL_NAME', 'gemini-2.5-flash'),
            gemini_api_key=os.getenv('GEMINI_API_KEY', '')
        )
        
        return cls(model_name=config.model_name, api_key=config.gemini_api_key, mcp_handler=mcp_handler)
    
    def create_chat_session(self, 
                          system_instruction: str, 
                          history: Optional[List[Dict]] = None,
                          thinking_budget: int = 0,
                          assistant_name: str = "AZOR") -> GeminiChatSessionWrapper:
        """
        Creates a new chat session with the specified configuration.
        
        Args:
            system_instruction: System role/prompt for the assistant
            history: Previous conversation history (optional, in universal dict format)
            thinking_budget: Thinking budget for the model
            
        Returns:
            GeminiChatSessionWrapper with universal dictionary-based interface
        """
        if not self._model:
            raise RuntimeError("LLM model not initialized")
        
        self.system_instruction = system_instruction
        
        # Convert universal dict format to Gemini Content objects
        gemini_history = []
        if history:
            for entry in history:
                if isinstance(entry, dict) and 'role' in entry and 'parts' in entry:
                    text = entry['parts'][0].get('text', '') if entry['parts'] else ''
                    if text:
                        content = glm.Content(
                            role=entry['role'],
                            parts=[glm.Part(text=text)] # Direct instantiation of Part with text
                        )
                        gemini_history.append(content)
        
        # Use start_chat with the model directly
        gemini_session = self._model.start_chat(
            history=gemini_history,
            # system_instruction is passed directly to the model as the first message or as a parameter if supported
            # For now, we will prepend it to the history if it's not empty, or pass as a separate config
            enable_automatic_function_calling=False # Disable automatic function calling - we handle it manually
        )
        
        return GeminiChatSessionWrapper(gemini_session, assistant_name)
    
    def count_history_tokens(self, history: List[Dict]) -> int:
        """
        Counts tokens for the given conversation history.
        
        Args:
            history: Conversation history in universal dict format
            
        Returns:
            Total token count
        """
        if not history:
            return 0
        
        try:
            # Convert universal dict format to Gemini Content objects for token counting
            gemini_history = []
            for entry in history:
                if isinstance(entry, dict) and 'role' in entry and 'parts' in entry:
                    text = entry['parts'][0].get('text', '') if entry['parts'] else ''
                    if text:
                        content = glm.Content(
                            role=entry['role'],
                            parts=[glm.Part(text=text)] # Direct instantiation of Part with text
                        )
                        gemini_history.append(content)
            
            response = self._model.count_tokens(
                contents=gemini_history
            )
            return response.total_tokens
        except Exception as e:
            console.print_error(f"Błąd podczas liczenia tokenów: {e}")
            return 0
    
    def get_model_name(self) -> str:
        """
        Returns the currently configured model name.
        """
        return self.model_name
    
    def is_available(self) -> bool:
        """
        Checks if the LLM service is available and properly configured.
        
        Returns:
            True if client is properly initialized and has API key
        """
        return self._model is not None and bool(self.api_key)
    
    def ready_for_use_message(self) -> str:
        """
        Returns a ready-to-use message with model info and masked API key.
        
        Returns:
            Formatted message string for display
        """
        # Mask API key - show first 4 and last 4 characters
        if len(self.api_key) <= 8:
            masked_key = "****"
        else:
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}"
        
        return f"✅ Klient Gemini gotowy do użycia (Model: {self.model_name}, Key: {masked_key})"
    
    def generate_title_text(self, prompt: str) -> str:
        """
        Generates text (title) based on a prompt using the model's single-turn API.
        
        Args:
            prompt: Prompt text containing the request for the title.
            
        Returns:
            The generated title text.
        """
        if not self._model:
            raise RuntimeError("LLM model not initialized")
        
        # Ustawienie instrukcji systemowej, która ma wymusić krótki i czysty tytuł
        system_instruction = (
            "Jesteś modułem odpowiedzialnym wyłącznie za generowanie krótkich, "
            "jednozdaniowych tytułów wątków. Odpowiedz tylko tytułem, bez otoczki, "
            "znaków interpunkcyjnych i dodatkowych komentarzy."
        )

        try:
            response = self._model.generate_content(
                contents=[prompt],
                generation_config=glm.GenerationConfig(
                    # system_instruction is passed directly to the model as the first message or as a parameter if supported
                    # For now, we will prepend it to the history if it's not empty, or pass as a separate config
                    temperature=0.1 
                )
            )
            
            # Wróć czysty tekst
            return response.text
            
        except Exception as e:
            # W przypadku błędu, zwrócenie pustego ciągu znaków (lub rzucenie wyjątku)
            console.print_error(f"Błąd podczas generowania tytułu: {e}")
            raise
        
    def get_system_prompt(self) -> str:
        """
        Returns the system instruction used for the current chat session.
        """
        return self.system_instruction
    
    # Removed client property since GenerativeModel is used directly
