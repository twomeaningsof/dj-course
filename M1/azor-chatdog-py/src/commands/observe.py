from session import get_session_manager
from cli import console
from cli.prompt import get_user_input
import google.generativeai as genai
import copy
from typing import List, Dict

def _construct_history_for_observer(session, current_assistant_name: str) -> List[Dict]:
    """
    Constructs a chat history compatible with Gemini API for the observer mode.
    It transforms messages from the 'other' assistant into User messages so the current
    assistant feels compelled to reply to them.
    
    Args:
        session: The current ChatSession.
        current_assistant_name: The name of the assistant currently generating a response.
        
    Returns:
        List of dicts with 'role' and 'parts'.
    """
    gemini_history = []
    
    for entry in session._history:
        role = entry['role']
        # Extract text safely
        text = ""
        if 'parts' in entry and entry['parts']:
            text = entry['parts'][0].get('text', "")
        
        assistant = entry.get('assistant_name')
        
        if role == 'user':
            gemini_history.append({'role': 'user', 'parts': [{'text': text}]})
        elif role == 'model':
            if assistant == current_assistant_name:
                # Own message -> Model role
                gemini_history.append({'role': 'model', 'parts': [{'text': text}]})
            else:
                # Other assistant's message -> User role (attributed)
                # We prefix with the name to give context
                attributed_text = f"[{assistant} powiedzial]: {text}" if assistant else text
                gemini_history.append({'role': 'user', 'parts': [{'text': attributed_text}]})
                
    return gemini_history

def _generate_response(system_prompt: str, history: List[Dict]) -> str:
    """
    Generates a response using a fresh Gemini model instance to ensure the correct system prompt is used.
    """
    # Use a default model name or get it from config if possible
    # For now hardcoded to match the project default
    model_name = "gemini-2.5-flash" 
    
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )
    
    try:
        response = model.generate_content(
            contents=history,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7 
            )
        )
        return response.text
    except Exception as e:
        return f"Error generating content: {e}"

def observe_command(args: str):
    """
    Starts an observation session between two assistants on a given topic.
    """
    manager = get_session_manager()
    available_assistants = manager.get_available_assistant_types()
    
    parts = args.split(maxsplit=2)
    
    if len(parts) < 3:
        console.print_error("Twoje polecenie jest niekompletne. Wymagany format: /observe <ASSISTANT_A> <ASSISTANT_B> <TOPIC>")
        console.print_info(f"Dostępni asystenci: {', '.join(available_assistants)}")
        return

    assistant_a_key = parts[0].upper()
    assistant_b_key = parts[1].upper()
    topic = parts[2]

    if assistant_a_key not in available_assistants or assistant_b_key not in available_assistants:
        console.print_error("Nieznany asystent.")
        return

    if assistant_a_key == assistant_b_key:
        console.print_error("Asystenci muszą być różni.")
        return

    # Start new session with Assistant A initially
    console.print_info(f"\nRozpoczynam obserwację: {assistant_a_key} vs {assistant_b_key}")
    console.print_info(f"Temat: {topic}\n")
    
    session, _, _, _ = manager.create_new_session(save_current=True, assistant_type=assistant_a_key)
    session.rename(f"Observation: {assistant_a_key} vs {assistant_b_key}")
    
    # Manually insert TOPIC as the first User message
    initial_user_entry = {"role": "user", "parts": [{"text": topic}]}
    session._history.append(initial_user_entry)
    session._initialize_llm_session() # SYNC: Update LLM session with new history
    session.save_to_file()

    # Get assistant instances to access system prompts
    # We do this via a temporary lookup or by creating instances
    # We can reuse the manager's factory logic
    create_a = manager._get_assistant_creator(assistant_a_key)
    create_b = manager._get_assistant_creator(assistant_b_key)
    
    assistant_a_instance = create_a()
    assistant_b_instance = create_b()
    
    assistants = {
        assistant_a_key: assistant_a_instance,
        assistant_b_key: assistant_b_instance
    }

    # Loop setup
    # Assistant A goes first
    speakers_order = [assistant_a_key, assistant_b_key]
    
    try:
        while True:
            for speaker_key in speakers_order:
                current_assistant = assistants[speaker_key]
                
                # Update session assistant for correct metadata saving
                session.set_assistant(current_assistant)
                
                # Construct history view for this speaker
                # (Counterpart messages become User messages)
                conversation_context = _construct_history_for_observer(session, current_assistant.name)
                
                # Generate response
                console.print_info(f"\n--- {current_assistant.name} Turn ---")
                response_text = _generate_response(current_assistant.system_prompt, conversation_context)
                
                console.print_assistant(f"{current_assistant.name}: {response_text}")
                
                # Append to session history as MODEL (No user duplication!)
                model_entry = {
                    "role": "model",
                    "parts": [{"text": response_text}],
                    "assistant_name": current_assistant.name
                }
                session._history.append(model_entry)
                session._initialize_llm_session() # SYNC: Update LLM session with new history
                session.save_to_file()
            
            # Prompt after both have spoken
            console.print_info("\n-- Czy kontynuować dyskusję? (t/n) --")
            user_choice = get_user_input().lower().strip()
            
            if user_choice not in ['t', 'y', 'tak', 'yes', 'jacha']:
                console.print_info("Zakończono obserwację.")
                break
                
    except KeyboardInterrupt:
        console.print_info("\nPrzerwano obserwację.")
    except Exception as e:
        console.print_error(f"Wystąpił błąd podczas obserwacji: {e}")
