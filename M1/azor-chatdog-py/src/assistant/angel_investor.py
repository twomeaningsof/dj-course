"""
Azor Assistant Configuration
Contains Azor-specific factory function.
"""

from .assistent import Assistant

def create_angel_investor_assistant() -> Assistant:
    """
    Creates and returns an Angel Investor assistant instance with default configuration.
    
    Returns:
        Assistant: Configured Angel Investor assistant instance
    """
    # Assistant name displayed in the chat
    assistant_name = "ANGEL INVESTOR"
    
    system_role = """
        Jesteś niecierpliwym inwestorem technologicznym. Twoje cechy:
        - Skupienie wyłącznie na biznesie, zyskach (ROI) i skalowalności.
        - Komunikacja "straight to the point" - uciananie zbędnych opisów i lania wody.
        - Brak zainteresowania detalami technicznymi (twój background IT jest nieaktualny).
        - Popieranie pomysłu tylko wtedy, gdy liczby i logika rynkowa wskazują na wysoki potencjał zysku.
        - Okazywanie irytacji przy braku konkretów.
        """
  
    return Assistant(
        system_prompt=system_role,
        name=assistant_name
    )
