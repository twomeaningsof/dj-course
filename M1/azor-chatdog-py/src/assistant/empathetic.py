"""
Azor Assistant Configuration
Contains Azor-specific factory function.
"""

from .assistent import Assistant

def create_empathetic_assistant() -> Assistant:
    """
    Creates and returns an Empathetic assistant instance with default configuration.
    
    Returns:
        Assistant: Configured Empathetic assistant instance
    """
    # Assistant name displayed in the chat
    assistant_name = "EMPATHETIC"
    
    # System role/prompt for the assistant
    system_role = "Jesteś optymistycznym pochlebcą, który zawsze pocieszy i dopytuje jak ktoś się czuje."
    
    return Assistant(
        system_prompt=system_role,
        name=assistant_name
    )
