"""Celery tasks for worker and beat"""

import datetime
import os
from tempfile import mkdtemp

from paperglobe import PaperGlobe
from celery.schedules import crontab

from app.factories import create_app, init_celery
from app.database import ConversionJob, db
from app.utils import generate_export_dir_name


app = create_app()
celery_app = init_celery(app)

# pylint: disable=unused-argument
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setter for periodic tasks"""
    sender.add_periodic_task(
        crontab(hour=6),
        remove_old_jobs.s(),
    )


@celery_app.task(bind=True)
def convert_to_template(self, file_path, file_id, image_format, image_projection):
    """Main worker for this app.

       - Gets the file info
       - Handles the conversion
       - Updates the database object

    Parameters
    ----------

    file_path : string
        path of the image file
    file_id : string (UUID4)
        UUID of the file/job
    image_format : str
        printing size of the template. one of:
            - "a4"
            - "us-letter"
    image_projection : str
        type of projection. one of:
            - "equirectangular"
            - "mercator"
            - "gall-stereo"
    """
    task_id = self.request.id

    export_dir = os.environ.get("EXPORT_DIR", mkdtemp())

    dir_name = generate_export_dir_name(file_id)
    export_path = os.path.join(export_dir, dir_name, "")
    os.mkdir(export_path)

    conversion_job = ConversionJob.query.get(file_id)
    conversion_job.job_id = task_id
    db.session.commit()

    def echo_status(status_type, message):
        conversion_job.message = message
        conversion_job.status = status_type
        db.session.commit()

    def bold(text):
        return f"<strong>{text}</strong>"

    paper_globe = PaperGlobe(on_update=echo_status, bold=bold)
    out_path = paper_globe.generate_paperglobe(
        file_path,
        image_projection,
        image_format,
        export_path
    )

    if os.path.exists(out_path[0]) is True:
        export_url = os.path.join(dir_name, out_path[1])

        conversion_job.export_file_path = out_path[0]
        conversion_job.export_url = export_url
        db.session.commit()


@celery_app.task
def remove_old_jobs():
    """Daily beat job. Removes objects older than 1 week and deleted objects."""

    current_time = datetime.datetime.utcnow()
    one_week_ago = current_time - datetime.timedelta(weeks=1)

    ConversionJob.query.filter(ConversionJob.start_date > one_week_ago).delete()
    ConversionJob.query.filter(ConversionJob.deleted.is_(True)).delete()
    db.session.commit()
