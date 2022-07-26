"""App initialization and routes"""

import datetime
import logging.config
import os

import click
from celery.result import AsyncResult
from flask import (
    abort,
    make_response,
    redirect,
    render_template,
    request,
    session,
)
from flask_assets import Environment, Bundle
from flask_babel import Babel
from flask_htmx import HTMX
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import desc

from app.database import db, ConversionJob, FormatsEnum, ProjectionsEnum
from app.controllers import (
    upload_controller,
    admin_delete_controller,
    admin_revert_controller,
)
from app.factories import create_app
from app.tasks import convert_to_template
from app.utils import is_uuid_valid
from app.forms import UploadForm

app = create_app()

# Assets config
assets = Environment(app)
assets.debug = app.debug
bundles = {
    "css": Bundle(
        "vendor/*.css",
        "app/static/src/inter.css",
        "app/static/src/main.css",
        output="dist/styles.css",
        filters="cssmin",
    ),
    "js": Bundle(
        "vendor/*.js",
        output="dist/scripts.js",
        filters="jsmin",
    ),
}
assets.register(bundles)
assets.load_path = "."

# Rate limiter config
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri=app.config["REDIS_BROKER_URL"],
    strategy="fixed-window",  # or "moving-window"
)

# Logger config
logging.config.dictConfig(app.config["DICT_LOGGER"])

# Database config
migrate = Migrate(app, db)

# HTMX config
htmx = HTMX(app)

# CRSF config
csrf = CSRFProtect(app)

# i18n config
babel = Babel(app)


@babel.localeselector
def get_locale():
    """Get language pref from session, or from best match"""
    language = session.get("language", None)
    if language is not None:
        return language
    return request.accept_languages.best_match(app.config["LANGUAGES"].keys())


@app.context_processor
def inject_conf_var():
    """Injects languages in the context"""
    return dict(
        AVAILABLE_LANGUAGES=app.config["LANGUAGES"],
        CURRENT_LANGUAGE=session.get(
            "language",
            request.accept_languages.best_match(app.config["LANGUAGES"].keys()),
        ),
    )


@app.before_request
def set_language():
    """Sets language if request contains 'lang' POST argument"""
    if request.args.get("lang", None) in app.config["LANGUAGES"].keys():
        session["language"] = request.args["lang"]


@app.template_filter("datetimeformat")
def datetime_format(value, date_format="%y-%m-%d %H:%M"):
    """Date transformation template filter"""
    return value.strftime(date_format) if value else value


@app.template_filter("as_dict")
def as_dict(obj):
    """Date transformation template filter"""
    return obj.as_dict() if hasattr(obj, "as_dict") else obj


@app.before_first_request
def make_session_permanent():
    """Sets the session as permanent (1 week)"""
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(weeks=1)


@app.errorhandler(404)
def page_not_found(error):
    """Handles 404 errors"""
    return render_template("error.html", error=error), 404


@app.errorhandler(500)
def page_error(error):
    """Handles 500 errors"""
    return render_template("error.html", error=error), 500


@app.route("/")
@limiter.exempt
def index():
    """Application index

    Checks the session and redirects to the last result if session is present
    Otherwise, displays the main form
    """
    form = UploadForm()
    if "file_id" in session:
        file_id = session["file_id"]
        try:
            assert is_uuid_valid(file_id)
            job = ConversionJob.query.filter_by(id=file_id).first()
            assert job is not None
        except (AssertionError, ValueError):
            return render_template("index.html", form=form)
        else:
            return redirect(f"/result/{file_id}")

        session.pop("file_id", None)

    return render_template("index.html", form=form)


@app.route("/new", methods=["GET", "POST"])
def new():
    """Upload form route

    GET
        Displays the main form

    POST
        If the form is valid:
            - Will call the image treatment task if the form is valid
            - Will set a session var with the job ID
    """
    form = UploadForm()

    if request.method == "GET":
        return render_template("index.html", form=form)

    if request.method == "POST":
        if form.validate_on_submit():

            image_url = form.image_url.data
            image_file = form.image_file.data
            image_preset = form.image_preset.data
            image_type = form.image_type.data

            print_format = form.print_format.data
            projection = form.projection.data

            if image_type == "upload":
                file_path, file_id, status = upload_controller(
                    file_object=image_file,
                    print_format=print_format,
                    projection=projection,
                )

            elif image_type == "preset":
                file_path, file_id, status = upload_controller(
                    file_preset=image_preset,
                    print_format=print_format,
                    projection=projection,
                )

            elif image_url != "":
                file_path, file_id, status = upload_controller(
                    file_url=image_url,
                    print_format=print_format,
                    projection=projection,
                )

            session["file_id"] = file_id

            if status != "error":
                convert_to_template.delay(file_path, file_id, print_format, projection)

            if htmx:
                job = ConversionJob.query.filter_by(id=file_id).first_or_404()
                resp = make_response(render_template("partials/poll.html", job=job))
                resp.headers["HX-Push-Url"] = f"/result/{file_id}"
                return resp

            return redirect(f"/result/{file_id}")

    if htmx:
        return render_template("partials/form.html", form=form)

    return render_template("index.html", form=form)


@app.route("/instructions")
@limiter.exempt
def instructions():
    """Displays the instructions page"""
    return render_template("instructions.html")


@app.route("/<admin_key>/admin")
@limiter.exempt
def admin(admin_key):
    """Displays the admin view

    The URL is protected by a key defined in the env var `ADMIN_KEY`
    """
    if admin_key != app.config["ADMIN_KEY"]:
        abort(404)

    jobs = ConversionJob.query.filter(ConversionJob.deleted.is_not(True)).order_by(
        desc(ConversionJob.start_date)
    )

    deleted_jobs = ConversionJob.query.filter(ConversionJob.deleted.is_(True)).order_by(
        desc(ConversionJob.start_date)
    )

    return render_template("admin.html", jobs=jobs, deleted_jobs=deleted_jobs)


@app.route("/<admin_key>/delete", methods=["POST"])
@limiter.exempt
def admin_delete(admin_key):
    """Deletes a job/image object from post data

    The URL is protected by a key defined in the env var `ADMIN_KEY`
    """
    if admin_key != app.config["ADMIN_KEY"]:
        abort(404)

    job_id = request.form.get("job_id")

    admin_delete_controller(job_id)

    return redirect(f"/{admin_key}/admin")


@app.route("/<admin_key>/revert", methods=["POST"])
@limiter.exempt
def admin_revert(admin_key):
    """Reverts a deleted job/image object from post data

    The URL is protected by a key defined in the env var `ADMIN_KEY`
    """
    if admin_key != app.config["ADMIN_KEY"]:
        abort(404)

    job_id = request.form.get("job_id")

    admin_revert_controller(job_id)

    return redirect(f"/{admin_key}/admin")


@app.route("/result/<file_id>")
@limiter.exempt
def result(file_id):
    """Displays the result for the job specified by the URL"""
    if not is_uuid_valid(file_id):
        return redirect("/new")

    job = ConversionJob.query.filter_by(id=file_id).first_or_404()

    return render_template("result.html", job=job)


@app.route("/poll/<file_id>")
@limiter.exempt
def poll(file_id):
    """Results polling utility

    Returns a view along with a custom header depending on the job status
    """
    if not is_uuid_valid(file_id):
        return redirect("/new")

    job = ConversionJob.query.filter_by(id=file_id).first_or_404()

    task_status = "PENDING"
    if job.job_id:
        task = AsyncResult(job.job_id)
        task_status = task.status

    if (
        job.status == "success"
        or job.export_url is not None
        or task_status == "SUCCESS"
    ):
        return render_template("partials/success.html", job=job)

    if job.status == "error" or task_status == "FAILURE":
        session["file_id"] = None

        return render_template("partials/failure.html", job=job)

    return render_template("partials/loading.html", job=job)


@app.cli.group()
def admin():
    """Administration commands."""
    pass


@admin.command()
def retry_started():
    """Retry tasks that have been started but have no job_id."""
    jobs = ConversionJob.query.filter(ConversionJob.job_id.is_(None))

    if jobs.count() == 0:
        print("No jobs to retry")
        pass

    for job in jobs:
        file_path = job.origin_file_path
        file_id = job.id
        print_format = job.print_format if job.print_format else FormatsEnum.A4
        projection = (
            job.projection if job.projection else ProjectionsEnum.EQUIRECTANGULAR
        )
        print(f"{file_id} started")

        convert_to_template.delay(
            file_path, file_id, print_format.value, projection.value
        )


@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
def update():
    """Update all languages."""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extract command failed")
    if os.system("pybabel update -i messages.pot -d app/translations"):
        raise RuntimeError("update command failed")
    os.remove("messages.pot")


@translate.command()
def compile():
    """Compile all languages."""
    if os.system("pybabel compile -d app/translations"):
        raise RuntimeError("compile command failed")


@translate.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language."""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extract command failed")
    if os.system("pybabel init -i messages.pot -d app/translations -l " + lang):
        raise RuntimeError("init command failed")
    os.remove("messages.pot")


if __name__ == "__main__":
    app.run()
