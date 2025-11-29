from cli import console
from session.session_manager import SessionManager

def rename_session_command(session_manager: SessionManager, new_title: str):
    """
    Obsługuje komendę CLI do zmiany tytułu bieżącej sesji.

    Args:
        session_manager: Instancja SessionManager.
        new_title: Nowy tytuł sesji.
    """
    if not new_title:
        console.print_error("Wymagany jest nowy tytuł. Użyj: /rename [nowy tytuł]")
        return

    # Ograniczenie długości tytułu (opcjonalne)
    if len(new_title.strip()) > 100:
        console.print_error("Tytuł jest za długi. Maksymalnie 100 znaków.")
        return
        
    try:
        success, error = session_manager.rename_current_session(new_title.strip())
        
        if success:
            console.print_info(f"Tytuł sesji zmieniony na: '{new_title.strip()}'")
        else:
            console.print_error(f"Nie udało się zmienić tytułu: {error or 'Nieznany błąd zapisu.'}")

    except RuntimeError as e:
        console.print_error(f"Błąd: {e}")
        
    except Exception as e:
        console.print_error(f"Nieoczekiwany błąd: {e}")