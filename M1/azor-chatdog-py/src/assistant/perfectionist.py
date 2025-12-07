"""
Azor Assistant Configuration
Contains Azor-specific factory function.
"""

from .assistent import Assistant

def create_perfectionist_assistant() -> Assistant:
    """
    Creates and returns an Perfectionist assistant instance with default configuration.
    
    Returns:
        Assistant: Configured Perfectionist assistant instance
    """
    # Assistant name displayed in the chat
    assistant_name = "PERFECTIONIST"
    
    # System role/prompt for the assistant
    system_role = "Jesteś perfekcjonistą przykładającym ogromną wagę do detali. Jeśli coś nie jest jasne, to zawsze chcesz to doprecyzować."
    
    return Assistant(
        system_prompt=system_role,
        name=assistant_name
    )
