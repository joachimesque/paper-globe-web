"""Low-level utilities"""
import xml.etree.ElementTree as et
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


def is_svg(file_path):
    """Returns SVG check as boolean"""

    tag = None
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            for event, element in et.iterparse(file, ("start",)):
                tag = element.tag
                break
        except et.ParseError:
            pass
    return tag == "{http://www.w3.org/2000/svg}svg"
