"""App initialization and routes"""

import logging.config

from flask import (
    abort,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_assets import Environment, Bundle
from flask_migrate import Migrate
from turbo_flask import Turbo
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import desc

from app.database import db, ConversionJob
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
        "src/chota.css",
        "src/inter.css",
        "src/main.css",
        output="dist/styles.css",
        filters="cssmin",
    ),
    "stimulus": Bundle("src/stimulus.js", output="dist/stimulus.js", filters="jsmin"),
}
assets.register(bundles)

# Rate limiter config
limiter = Limiter(
    app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

# Logger config
logging.config.dictConfig(app.config["DICT_LOGGER"])

# Database config
migrate = Migrate(app, db)

# Turbo config
turbo = Turbo(app)

# CRSF config
csrf = CSRFProtect(app)


@app.template_filter("datetimeformat")
def datetime_format(value, date_format="%y-%m-%d %H:%M"):
    """Date transformation template filter"""
    return value.strftime(date_format) if value else value


@app.before_first_request
def make_session_permanent():
    """Sets the session as permanent (30 days)"""
    session.permanent = True


@app.errorhandler(404)
def page_not_found(error):
    """Handles 404 errors"""
    return render_template("error.html", error=error), 404


@app.errorhandler(500)
def page_not_found(error):
    """Handles 500 errors"""
    return render_template("error.html", error=error), 500


@app.route("/")
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


@app.route("/new")
def new():
    """Displays the main form"""
    form = UploadForm()

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

    if job.status == "success" or job.export_url is not None:
        resp = make_response(render_template("partials/success.html", job=job))
        resp.headers["X-Custom-Status"] = "Success"
        return resp

    if job.status == "error":
        session["file_id"] = None

        resp = make_response(render_template("partials/failure.html", job=job))
        resp.headers["X-Custom-Status"] = "Error"
        return resp

    resp = make_response(render_template("partials/loading.html", job=job))
    resp.headers["X-Custom-Status"] = "Wait"
    return resp


@app.route("/upload", methods=["POST"])
def upload_image():
    """Upload form endpoint

    If the form is valid:
        - Will call the image treatment task if the form is valid
        - Will set a session var with the job ID
    """
    form = UploadForm()

    if not form.validate_on_submit():
        return redirect(request.url)

    image_url = form.image_url.data
    image_file = form.image_file.data
    image_type = form.image_type.data

    print_format = form.print_format.data
    projection = form.projection.data

    if image_type == "upload":
        if not image_file:
            return redirect(request.url)

        file_path, file_id = upload_controller(file_object=image_file)

    elif image_url != "":
        file_path, file_id = upload_controller(file_url=image_url)

    else:
        return redirect(request.url)

    convert_to_template.delay(file_path, file_id, print_format, projection)

    session["file_id"] = file_id

    return redirect(f"/result/{file_id}")


if __name__ == "__main__":
    app.run()
