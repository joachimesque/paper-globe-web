"""Forms"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import URLField, RadioField
from wtforms.validators import DataRequired, Optional

from paperglobe import PROJECTIONS, PRINT_SIZES

image_type_choices = [
    ("preset", "select preset"),
    ("upload", "upload image"),
    ("url", "paste url"),
]
image_preset_choices = [
    ("earth.jpg", "Earth, physical"),
    ("earth-countries.svg", "Earth, political"),
    ("mars.jpg", "Mars"),
    ("moon.jpg", "Moon"),
]
print_format_choices = [(name, name) for item, name in PRINT_SIZES.items()]
projection_choices = [(name, name) for item, name in PROJECTIONS.items()]


class RequiredIf(DataRequired):
    """Validator which makes a field required if another field is set and has a truthy value.
    https://gist.github.com/devxoul/7638142?permalink_comment_id=2601001#gistcomment-2601001

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
        - https://gist.github.com/devxoul/7638142#file-wtf_required_if-py
    """
    field_flags = ('requiredif',)

    def __init__(self, message=None, *args, **kwargs):
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


class UploadForm(FlaskForm):
    """Image upload/link form"""

    image_url = URLField("Paste your image URL", validators=[RequiredIf(image_type="url")])
    image_file = FileField(
        "Upload your image file",
        validators=[
            FileAllowed(["jpg", "png", "svg"], "Images only!"),
            RequiredIf(image_type="upload")
        ],
    )
    image_preset = RadioField(
        "Select a preset",
        choices=image_preset_choices,
        default=image_preset_choices[0][0],
        validators=[
            RequiredIf(image_type="preset")
        ]
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
