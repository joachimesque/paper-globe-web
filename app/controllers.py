"""Controllers for the app"""

import os
import imghdr
import uuid
import shutil
from tempfile import mkdtemp
from urllib.parse import urlparse, unquote_plus

from flask import abort
import requests

from app.database import db, ConversionJob, FormatsEnum, ProjectionsEnum
from app.utils import generate_export_dir_name, generate_secure_filename, is_svg


def admin_delete_controller(job_id):
    """Controller for the admin delete route

    This will
        - add a deleted tag to the object
        - move the export file to a new path

    Arguments
    ---------

    job_id : string
        The id of a job (UUID4 as string)
    """

    job = ConversionJob.query.get_or_404(job_id)
    if job.deleted:
        abort(404)
    job.deleted = True

    if job.export_file_path and os.path.exists(job.export_file_path):
        export_dir = os.environ.get("EXPORT_DIR", mkdtemp())
        dir_name = generate_export_dir_name(job.id)
        new_file_dir = os.path.join(export_dir, "deleted", dir_name)
        new_file_path = os.path.join(export_dir, "deleted", job.export_url)

        if not os.path.exists(new_file_dir):
            os.mkdir(new_file_dir)

        os.rename(job.export_file_path, new_file_path)

        job.export_file_path = new_file_path

    db.session.commit()


def admin_revert_controller(job_id):
    """Controller for the admin revert route

    This will
        - remove the object's deleted tag
        - move the export file to its right path

    Arguments
    ---------

    job_id : string
        The id of a job (UUID4 as string)
    """

    job = ConversionJob.query.get_or_404(job_id)
    if job.deleted is False:
        abort(404)
    job.deleted = False

    if job.export_file_path and os.path.exists(job.export_file_path):
        export_dir = os.environ.get("EXPORT_DIR", mkdtemp())
        dir_name = generate_export_dir_name(job.id)
        new_file_dir = os.path.join(export_dir, dir_name)
        new_file_path = os.path.join(export_dir, job.export_url)

        if not os.path.exists(new_file_dir):
            os.mkdir(new_file_dir)

        os.rename(job.export_file_path, new_file_path)

        job.export_file_path = new_file_path

    db.session.commit()


def upload_controller(
    file_url=None,
    file_object=None,
    file_preset=None,
    print_format=FormatsEnum.A4,
    projection=ProjectionsEnum.EQUIRECTANGULAR,
):
    """Controller for the upload route

    Depending on the argument received, this will
        - save the file object payload as an image file
        - download and save the image file from the URL
        - copy the preset to a temp file
    Then it will initialize the object in the DB and return info for the task

    Arguments
    ---------

    file_url : string
        The URL for a file available on the WWW

    file_object : object
        File object of an uploaded file

    file_preset : string
        Filename of a preset file

    print_format : str
        printing size of the template. one of:
            - "a4" (default)
            - "us-letter"
    projection : str
        type of projection. one of:
            - "equirectangular" (default)
            - "mercator"
            - "gall-stereo"

    Returns
    -------

    tuple : (string, string, string)
        - file path
        - ID for the file/job
        - status
    """
    temp_dir = mkdtemp()

    file_id = str(uuid.uuid4())

    if file_object is not None:
        file_name = generate_secure_filename(file_object.filename)
        file_path = os.path.join(temp_dir, file_name)
        file_object.save(file_path)

    if file_preset is not None:
        static_dir = os.environ.get("STATIC_DIR")
        preset_path = os.path.join(static_dir, "presets", file_preset)
        file_name = generate_secure_filename(file_preset)
        file_path = os.path.join(temp_dir, file_preset)

        shutil.copy(preset_path, file_path)

    if file_url is not None:
        parsed_path = urlparse(unquote_plus(file_url)).path
        file_name = generate_secure_filename(os.path.basename(parsed_path))
        file_path = os.path.join(temp_dir, file_name)

        response = requests.get(file_url)
        with open(file_path, "wb") as file:
            file.write(response.content)

    if imghdr.what(file_path) is not None or is_svg(file_path):
        status = "started"
        message = f"We’re transfering <strong>{file_name}</strong> to the transmogrificator 🧑‍🚀"
    else:
        status = "error"
        message = (
            f"The file <strong>{file_name}</strong> is not an image. Please try again"
        )

    conversion_job = ConversionJob(
        id=file_id,
        origin_file_path=file_path,
        message=message,
        status=status,
        print_format=FormatsEnum(print_format),
        projection=ProjectionsEnum(projection),
    )
    db.session.add(conversion_job)
    db.session.commit()

    return (file_path, file_id, status)
