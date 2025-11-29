import json
import os
from typing import List, Any, Tuple, Optional
from files.config import LOG_DIR 


def _get_session_path(session_id: str) -> str:
    """Pomocnicza funkcja zwracająca pełną ścieżkę do pliku sesji."""
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    return os.path.join(LOG_DIR, f"{session_id}.json")

def save_session_history(
    session_id: str, 
    history: List[Any], 
    system_prompt: str, 
    model_name: str, 
    title: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Zapisuje dane sesji, włącznie z tytułem, do pliku JSON w LOG_DIR.
    
    Args:
        session_id: Unikalny identyfikator sesji.
        history: Lista wiadomości.
        system_prompt: Systemowy prompt użyty w sesji.
        model_name: Nazwa użytego modelu.
        title: Tytuł sesji (nowy argument).
        
    Returns:
        Krotka (sukces: bool, wiadomość o błędzie: Optional[str])
    """
    try:
        file_path = _get_session_path(session_id)
        
        data = {
            "session_id": session_id,
            "title": title,
            "model": model_name,
            "system_prompt": system_prompt,
            "history": history
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return True, None
    except Exception as e:
        return False, str(e)

def load_session_history(session_id: str) -> Tuple[Optional[List[Any]], Optional[str], Optional[str]]:
    """
    Ładuje historię sesji i metadane, włącznie z tytułem, z pliku JSON.
    
    Returns:
        Krotka (history: Optional[List[Any]], title: Optional[str], error_message: Optional[str])
    """
    try:
        file_path = _get_session_path(session_id)
        
        if not os.path.exists(file_path):
            return None, None, f"Session file not found: {session_id}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        history = data.get("history", [])
        title = data.get("title")  # Odczyt tytułu (obsługuje stare pliki bez tytułu)
        
        return history, title, None
        
    except json.JSONDecodeError:
        return None, None, f"Corrupted session file: {session_id}"
    except Exception as e:
        return None, None, str(e)

def list_sessions() -> List[dict]:
    """
    Zwraca listę wszystkich dostępnych sesji z ich ID i tytułami, 
    uwzględniając wymagane metadane (liczbę wiadomości).
    """
    sessions = []
    
    if not os.path.exists(LOG_DIR):
        return sessions
        
    for filename in os.listdir(LOG_DIR):
        if filename.endswith(".json"):
            try:
                file_path = os.path.join(LOG_DIR, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    history = data.get("history", [])
                    # Obliczamy liczbę wiadomości:
                    message_count = len(history)
                    
                    sessions.append({
                        "id": data.get("session_id", filename.replace(".json", "")),
                        "title": data.get("title", "Untitled Session"),
                        "model": data.get("model", "Unknown"),
                        # DODANE: Wymagany klucz
                        "messages_count": message_count,
                        # DODANE: Klucz last_activity (załóżmy, że używamy daty modyfikacji pliku)
                        "last_activity": os.path.getmtime(file_path) # Data modyfikacji pliku
                    })
            except:
                # Pomijamy pliki, których nie udało się odczytać
                continue
    return sessions