"""Database init and models"""

import os
import uuid

from sqlalchemy import Column, String, DateTime, Text, Boolean, event
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ConversionJob(db.Model):
    """Main object type"""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True))
    start_date = Column(DateTime(), default=func.now())
    end_date = Column(DateTime(), onupdate=func.now())
    origin_file_path = Column(String(128))
    export_file_path = Column(String(128))
    export_url = Column(String(256))
    message = Column(Text())
    status = Column(String(16))
    deleted = Column(Boolean(), default=False)

    def as_dict(self):
        """Dictionary representation of the Class"""
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def __repr__(self):
        return f"<ConversionJob {self.id} {self.status} {self.message}>"


# pylint: disable=unused-argument
@event.listens_for(db.session, "persistent_to_deleted")
def object_is_pending(session, obj):
    """Listener for ConversionJob object delete event

    This action will remove files linked to the model
    """

    if obj.origin_file_path and os.path.exists(obj.origin_file_path):
        os.remove(obj.origin_file_path)

    if obj.export_file_path and os.path.exists(obj.export_file_path):
        os.remove(obj.export_file_path)
