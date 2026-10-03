from datetime import datetime
from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from server.auth import current_user, login_required, owned_or_error
from server.extensions import db
from server.models import DataRequest, RequestNote, User
from server.validation import validate_credentials, validate_note, validate_request

api = Blueprint("api", __name__, url_prefix="/api")


def page_args(default_per_page=10, max_per_page=50):
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", default_per_page, type=int)
    return page, min(max(per_page, 1), max_per_page)


def pagination_payload(pagination, serializer):
    return {
        "items": [serializer(item) for item in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


@api.get("/health")
def health():
    return {"status": "ok", "service": "ClinicalFlow API"}


@api.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    errors, values = validate_credentials(data)
    if errors:
        return jsonify({"errors": errors}), 400
    if User.query.filter((User.email == values["email"]) | (User.username == values["username"])).first():
        return jsonify({"error": "An account with that username or email already exists."}), 409
    user = User(username=values["username"], email=values["email"])
    user.set_password(values["password"])
    db.session.add(user)
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    return jsonify({"user": user.to_dict()}), 201


@api.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    session.clear()
    session["user_id"] = user.id
    return jsonify({"user": user.to_dict()})


@api.delete("/logout")
def logout():
    session.clear()
    return "", 204


@api.get("/check_session")
def check_session():
    user = current_user()
    if not user:
        return jsonify({"error": "Authentication required."}), 401
    return jsonify({"user": user.to_dict()})


@api.get("/requests")
@login_required
def requests_index():
    user = current_user()
    page, per_page = page_args()
    query = DataRequest.query.filter_by(owner_id=user.id)
    status = request.args.get("status")
    priority = request.args.get("priority")
    request_type = request.args.get("request_type")
    search = (request.args.get("search") or "").strip()
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if request_type:
        query = query.filter_by(request_type=request_type)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(DataRequest.title.ilike(pattern), DataRequest.description.ilike(pattern)))
    pagination = query.order_by(DataRequest.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(pagination_payload(pagination, lambda item: item.to_dict()))


@api.post("/requests")
@login_required
def requests_create():
    data = request.get_json(silent=True) or {}
    errors, values = validate_request(data)
    if errors:
        return jsonify({"errors": errors}), 400
    record = DataRequest(owner=current_user(), **values)
    if record.status == "Completed":
        record.completed_at = datetime.utcnow()
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@api.get("/requests/<int:request_id>")
@login_required
def requests_show(request_id):
    record, error = owned_or_error(DataRequest, request_id, current_user().id)
    if error:
        return error
    result = record.to_dict()
    result["notes_url"] = f"/api/requests/{record.id}/notes?page=1&per_page=5"
    return jsonify(result)


@api.patch("/requests/<int:request_id>")
@login_required
def requests_update(request_id):
    record, error = owned_or_error(DataRequest, request_id, current_user().id)
    if error:
        return error
    data = request.get_json(silent=True) or {}
    errors, values = validate_request(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400
    previous_status = record.status
    for key, value in values.items():
        setattr(record, key, value)
    if record.status == "Completed" and previous_status != "Completed":
        record.completed_at = datetime.utcnow()
    elif record.status != "Completed":
        record.completed_at = None
    db.session.commit()
    return jsonify(record.to_dict())


@api.delete("/requests/<int:request_id>")
@login_required
def requests_delete(request_id):
    record, error = owned_or_error(DataRequest, request_id, current_user().id)
    if error:
        return error
    db.session.delete(record)
    db.session.commit()
    return "", 204


@api.get("/requests/<int:request_id>/notes")
@login_required
def notes_index(request_id):
    record, error = owned_or_error(DataRequest, request_id, current_user().id)
    if error:
        return error
    page, per_page = page_args(default_per_page=5)
    pagination = RequestNote.query.filter_by(request_id=record.id, owner_id=current_user().id).order_by(RequestNote.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(pagination_payload(pagination, lambda item: item.to_dict()))


@api.post("/requests/<int:request_id>/notes")
@login_required
def notes_create(request_id):
    record, error = owned_or_error(DataRequest, request_id, current_user().id)
    if error:
        return error
    errors, content = validate_note(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"errors": errors}), 400
    note = RequestNote(content=content, data_request=record, owner=current_user())
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@api.get("/notes/<int:note_id>")
@login_required
def notes_show(note_id):
    note, error = owned_or_error(RequestNote, note_id, current_user().id)
    if error:
        return error
    return jsonify(note.to_dict())


@api.patch("/notes/<int:note_id>")
@login_required
def notes_update(note_id):
    note, error = owned_or_error(RequestNote, note_id, current_user().id)
    if error:
        return error
    errors, content = validate_note(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"errors": errors}), 400
    note.content = content
    db.session.commit()
    return jsonify(note.to_dict())


@api.delete("/notes/<int:note_id>")
@login_required
def notes_delete(note_id):
    note, error = owned_or_error(RequestNote, note_id, current_user().id)
    if error:
        return error
    db.session.delete(note)
    db.session.commit()
    return "", 204


@api.errorhandler(IntegrityError)
def integrity_error(_error):
    db.session.rollback()
    return jsonify({"error": "The requested change conflicts with existing data."}), 409
