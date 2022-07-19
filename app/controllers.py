"""Controllers for the app"""

import os
import uuid
from tempfile import mkdtemp
from urllib.parse import urlparse

import requests
from werkzeug.utils import secure_filename

from app.database import db, ConversionJob


def upload_controller(file_url=None, file_object=None):
    """Controller for the upload route

    Depending on the argument received, this will
        - save the file object payload as an image file
        - download and save the image file from the URL
    Then it will initialize the object in the DB and return info for the task

    Arguments
    ---------

    file_url : string
        The URL for a file available on the WWW

    file_object : object
        File object of an uploaded file

    Returns
    -------

    tuple : (string, string)
        - file path
        - ID for the file/job
    """
    temp_dir = mkdtemp()

    file_id = str(uuid.uuid4())

    if file_object is not None:
        file_name = secure_filename(file_object.filename)
        file_path = os.path.join(temp_dir, file_name)
        file_object.save(file_path)

    if file_url is not None:
        file_name = os.path.basename(urlparse(file_url).path)
        file_path = os.path.join(temp_dir, file_name)

        response = requests.get(file_url)
        with open(file_path, "wb") as file:
            file.write(response.content)

    assert os.path.exists(file_path)

    status = "started"
    message = (
        f"We’re transfering <strong>{file_name}</strong> to the transmogrificator 🧑‍🚀"
    )

    conversion_job = ConversionJob(
        id=file_id,
        origin_file_path=file_path,
        message=message,
        status=status,
    )
    db.session.add(conversion_job)
    db.session.commit()

    return (file_path, file_id)
