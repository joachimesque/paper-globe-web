"""Forms"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import URLField, RadioField

from paperglobe import PROJECTIONS, PRINT_SIZES

image_type_choices = [
    ("preset", "select preset"),
    ("upload", "upload image"),
    ("url", "paste url"),
]
image_preset_choices = [
    ("earth.jpg", "Earth"),
    ("earth-countries.svg", "Earth Countries"),
    ("mars.jpg", "Mars"),
    ("moon.jpg", "Moon"),
]
print_format_choices = [(name, name) for item, name in PRINT_SIZES.items()]
projection_choices = [(name, name) for item, name in PROJECTIONS.items()]


class UploadForm(FlaskForm):
    """Image upload/link form"""

    image_url = URLField("Paste your image URL")
    image_file = FileField(
        "Upload your image file",
        validators=[FileAllowed(["jpg", "png", "svg"], "Images only!")],
    )
    image_preset = RadioField(
        "Select a preset",
        choices=image_preset_choices,
        default=image_preset_choices[0][0],
    )
    image_type = RadioField(
        "Image type", choices=image_type_choices, default=image_type_choices[0][0]
    )
    print_format = RadioField(
        "Print format", choices=print_format_choices, default=print_format_choices[0][0]
    )
    projection = RadioField(
        "Projection", choices=projection_choices, default=projection_choices[0][0]
    )
