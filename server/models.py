from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from server.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requests = db.relationship(
        "DataRequest",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    notes = db.relationship(
        "RequestNote",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256:600000",
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


class DataRequest(db.Model):
    __tablename__ = "data_requests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    request_type = db.Column(db.String(60), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    status = db.Column(db.String(30), nullable=False, default="New")
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at = db.Column(db.DateTime, nullable=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    owner = db.relationship("User", back_populates="requests")

    notes = db.relationship(
        "RequestNote",
        back_populates="data_request",
        cascade="all, delete-orphan",
        order_by="RequestNote.created_at.desc()",
    )

    def to_dict(self, include_notes=False):
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "request_type": self.request_type,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "owner_id": self.owner_id,
            "owner": self.owner.to_dict() if self.owner else None,
        }

        if include_notes:
            result["notes"] = [note.to_dict() for note in self.notes]

        return result


class RequestNote(db.Model):
    __tablename__ = "request_notes"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    request_id = db.Column(
        db.Integer,
        db.ForeignKey("data_requests.id"),
        nullable=False,
        index=True,
    )
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    data_request = db.relationship("DataRequest", back_populates="notes")
    owner = db.relationship("User", back_populates="notes")

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "request_id": self.request_id,
            "owner_id": self.owner_id,
            "owner": self.owner.to_dict() if self.owner else None,
        }