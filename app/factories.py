"""Factories for our Flask and Celery apps"""

import os

from celery import Celery
from flask import Flask

from .database import db


def init_celery(app):
    """Add Flask app context to celery.Task"""
    celery = Celery(
        "celery_app",
        include=["app.tasks"],
    )
    celery.autodiscover_tasks(["app.tasks"])
    celery.conf.update(app.config)

    TaskBase = celery.Task

    # pylint: disable=too-few-public-methods
    class ContextTask(TaskBase):
        """Define a new Task class to add Flask app context"""

        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery


def create_app():
    """Initializes Flask app"""
    app = Flask(__name__)
    app.config.from_object(os.environ["APP_SETTINGS"])

    db.init_app(app)
    # init_celery(app)
    return app
