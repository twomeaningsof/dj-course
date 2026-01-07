"""
Assistant module initialization
Exports the Assistant class and assistant factory functions.
"""

from .assistent import Assistant
from .azor import create_azor_assistant
from .empathetic import create_empathetic_assistant
from .perfectionist import create_perfectionist_assistant
from .angel_investor import create_angel_investor_assistant
from .sparing_partner import create_sparing_partner_assistant

__all__ = ['Assistant', 'create_azor_assistant', 'create_empathetic_assistant','create_perfectionist_assistant', 'create_angel_investor_assistant', 'create_sparing_partner_assistant']
