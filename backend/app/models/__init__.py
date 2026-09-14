"""ORM models package.

Importing the models here ensures they are registered on the shared metadata
before ``Base.metadata.create_all`` is called.
"""
from app.models.attendance import Attendance
from app.models.camera import Camera
from app.models.person import FaceEncoding, Person
from app.models.user import User

__all__ = ["Attendance", "Camera", "FaceEncoding", "Person", "User"]
