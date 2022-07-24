"""Low-level utilities"""
from uuid import UUID
from werkzeug.utils import secure_filename


def is_uuid_valid(text):
    """Simple uuid validation"""

    try:
        UUID(str(text), version=4)
    except ValueError:
        return False
    else:
        return True


def generate_export_dir_name(file_id):
    """Generate export dir name from UUID"""

    return "".join(file_id.split("-")[0:1])


def generate_secure_filename(file_name):
    """Generate secure and non-empty filename"""

    new_file_name = secure_filename(file_name)
    if new_file_name == "":
        new_file_name = "image_file"

    return new_file_name