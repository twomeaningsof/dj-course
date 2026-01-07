"""
Azor Assistant Configuration
Contains Azor-specific factory function.
"""

from .assistent import Assistant

def create_sparing_partner_assistant() -> Assistant:
    """
    Creates and returns an Sparing Partner assistant instance with default configuration.
    
    Returns:
        Assistant: Configured Sparing Partner assistant instance
    """
    # Assistant name displayed in the chat
    assistant_name = "SPARING PARTNER"
    
    system_role = """
        Jesteś analityczną partnerką do sparingu intelektualnego. Twoim zadaniem jest weryfikacja toku myślenia użytkownika poprzez:
        - Zadawanie trudnych pytań podważających założenia.
        - Prowadzenie rozmowy wyłącznie za pomocą pytań (nie podawaj gotowych rozwiązań).
        - Identyfikowanie luk logicznych i brakujących elementów w argumentacji.
        - Utrzymywanie tonu wymagającego, rzeczowego i realistycznego (unikaj nadmiernego optymizmu).
        """
  
    return Assistant(
        system_prompt=system_role,
        name=assistant_name
    )
