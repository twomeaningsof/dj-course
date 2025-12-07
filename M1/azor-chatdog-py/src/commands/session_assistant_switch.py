from cli import console
from session.session_manager import SessionManager
from typing import List

# Lista dostępnych typów asystentów dla walidacji i wyświetlania
# Musi odpowiadać kluczom w _ASSISTANT_FACTORY w SessionManager
AVAILABLE_ASSISTANTS: List[str] = ['AZOR', 'PERFECTIONIST', 'EMPATHETIC'] 

def session_assistant_switch(session_manager: SessionManager, new_assistant_type: str):
    """
    Obsługuje komendę CLI do przełączania typu asystenta w bieżącej sesji.

    Args:
        session_manager: Instancja SessionManager.
        new_assistant_type: Nowy typ asystenta (np. 'PERFECTIONIST').
    """
    if not new_assistant_type:
        console.print_error("Wymagany jest typ asystenta. Dostępne typy: " + ", ".join(AVAILABLE_ASSISTANTS))
        return

    # 1. Normalizacja i walidacja typu asystenta
    new_assistant_type = new_assistant_type.strip().upper()
    
    if new_assistant_type not in AVAILABLE_ASSISTANTS:
        console.print_error(f"Nieznany typ asystenta: '{new_assistant_type}'. Dostępne typy: " + ", ".join(AVAILABLE_ASSISTANTS))
        return

    try:
        # 2. Wywołanie logiki przełączania w SessionManager
        success, old_assistant_name, error = session_manager.switch_assistant(new_assistant_type)
        
        if success:
            console.print_info(f"Asystent sesji przełączony pomyślnie. Nowy asystent: **{new_assistant_type}** (Poprzedni: {old_assistant_name})")
            
            # Wskazówka: Po przełączeniu asystenta, warto wyświetlić nową instrukcję systemową
            new_system_prompt = session_manager.get_current_session().assistant.system_prompt
            console.print_info(f"Nowa instrukcja systemowa asystenta: '{new_system_prompt}'")
        else:
            console.print_error(f"Nie udało się przełączyć asystenta: {error or 'Nieznany błąd.'}")

    except RuntimeError as e:
        # Obsługa błędu 'No active session'
        console.print_error(f"Błąd: {e}")
        
    except Exception as e:
        console.print_error(f"Nieoczekiwany błąd podczas przełączania asystenta: {e}")