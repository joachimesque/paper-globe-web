"""Forms"""

import importlib
import os

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
import requests
from wtforms import URLField, RadioField
from wtforms.validators import DataRequired, Optional, ValidationError

from paperglobe import PROJECTIONS, PRINT_SIZES


class_object = os.environ["APP_SETTINGS"]
module_name, class_name = class_object.rsplit(".", maxsplit=1)
config_module = importlib.import_module(module_name)
mimetypes_allowed = getattr(config_module, class_name).MIMETYPES_ALLOWED

image_type_choices = [
    ("preset", _l("select preset")),
    ("upload", _l("upload image")),
    ("url", _l("paste url")),
]
image_preset_choices = [
    ("earth.jpg", _l("Earth, physical")),
    ("earth-countries.svg", _l("Earth, political")),
    ("mars.jpg", _l("Mars")),
    ("moon.jpg", _l("Moon")),
]
print_format_choices = [(name, name) for item, name in PRINT_SIZES.items()]
projection_choices = [(name, name) for item, name in PROJECTIONS.items()]


class RequiredIf(DataRequired):  # pylint: disable=R0903
    """Validator that makes a field required if another field is set and has a truthy value.
    https://gist.github.com/devxoul/7638142?permalink_comment_id=2601001#gistcomment-2601001

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
        - https://gist.github.com/devxoul/7638142#file-wtf_required_if-py
    """

    field_flags = ("requiredif",)

    def __init__(self, message=None, **kwargs):
        super(RequiredIf).__init__()
        self.message = message
        self.conditions = kwargs

    # field is requiring that name field in the form is data value in the form
    def __call__(self, form, field):
        for name, data in self.conditions.items():
            other_field = form[name]
            if other_field is None:
                raise Exception(f"no field named {name} in form")
            if other_field.data == data and not field.data:
                DataRequired.__call__(self, form, field)
            Optional()(form, field)


class MimeTypeAllowed:  # pylint: disable=R0903
    """Validator that checks the Content-Type header of a response for the given URL"""

    field_flags = ("MimeTypeAllowed",)

    def __init__(self, *args, message=None):
        super(MimeTypeAllowed).__init__()
        self.message = message
        self.mimetypes_allowed = args[0]

    def __call__(self, form, field):
        if field.data != "":
            response_head = requests.head(field.data)
            if response_head.headers["Content-Type"] not in self.mimetypes_allowed:
                raise ValidationError(self.message)


class UploadForm(FlaskForm):
    """Image upload/link form"""

    image_url = URLField(
        _l("Paste your image URL"),
        validators=[
            MimeTypeAllowed(
                mimetypes_allowed, message=_l("The linked file is not an image")
            ),
            RequiredIf(image_type="url"),
        ],
    )
    image_file = FileField(
        _l("Upload your image file"),
        validators=[
            FileAllowed(["jpg", "png", "svg"], _l("Images only!")),
            RequiredIf(image_type="upload"),
        ],
    )
    image_preset = RadioField(
        _l("Select a preset"),
        choices=image_preset_choices,
        default=image_preset_choices[0][0],
        validators=[RequiredIf(image_type="preset")],
    )
    image_type = RadioField(
        _l("Image type"),
        choices=image_type_choices,
        default=image_type_choices[0][0],
    )
    print_format = RadioField(
        _l("Print format"),
        choices=print_format_choices,
        default=print_format_choices[0][0],
    )
    projection = RadioField(
        _l("Projection"),
        choices=projection_choices,
        default=projection_choices[0][0],
    )
