"""Low-level utilities"""
from uuid import UUID


def is_uuid_valid(text):
    """Simple uuid validation"""

    try:
        UUID(str(text), version=4)
    except ValueError:
        return False
    else:
        return True
