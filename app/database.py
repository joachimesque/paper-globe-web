"""Database init and models"""

import enum
import os
import uuid

from paperglobe import PRINT_SIZES, PROJECTIONS
from sqlalchemy import Column, String, DateTime, Text, Boolean, event, Enum
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

FormatsEnum = enum.Enum("FormatsEnum", [(k, v) for k, v in PRINT_SIZES.items()])

ProjectionsEnum = enum.Enum("ProjectionsEnum", [(k, v) for k, v in PROJECTIONS.items()])


class ConversionJob(db.Model):
    """Main object type"""

    id = Column(String(), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    job_id = Column(String())
    start_date = Column(DateTime(), default=func.now())
    end_date = Column(DateTime(), onupdate=func.now())
    origin_file_path = Column(String(128))
    export_file_path = Column(String(128))
    export_url = Column(String(256))
    message = Column(Text())
    status = Column(String(16))
    deleted = Column(Boolean(), default=False)
    print_format = Column(Enum(FormatsEnum), default=FormatsEnum.A4)
    projection = Column(Enum(ProjectionsEnum), default=ProjectionsEnum.EQUIRECTANGULAR)

    def as_dict(self):
        """Dictionary representation of the Class"""
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def __repr__(self):
        return f"<ConversionJob '{self.id}' '{self.status}' '{self.message}'>"


# pylint: disable=unused-argument
@event.listens_for(db.session, "persistent_to_deleted")
def delete_linked_files(session, obj):
    """Listener for ConversionJob object delete event

    This action will permanently delete files linked to the model
    """
    for file_path in (obj.origin_file_path, obj.export_file_path):
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
