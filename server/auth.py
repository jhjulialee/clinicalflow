from functools import wraps
from flask import jsonify, session
from server.extensions import db
from server.models import User


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "Authentication required."}), 401
        return view(*args, **kwargs)
    return wrapped


def owned_or_error(model_class, record_id, user_id):
    record = db.session.get(model_class, record_id)
    if not record:
        return None, (jsonify({"error": "Record not found."}), 404)
    if record.owner_id != user_id:
        return None, (jsonify({"error": "You do not have permission to access this record."}), 403)
    return record, None
