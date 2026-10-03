from datetime import date

VALID_TYPES = {"Report", "Data Quality", "Dashboard", "Data Extract", "Other"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
VALID_STATUSES = {"New", "In Progress", "Blocked", "Completed"}


def validate_credentials(data, creating=True):
    errors = {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if creating and len(username) < 2:
        errors["username"] = "Username must contain at least 2 characters."
    if "@" not in email:
        errors["email"] = "Enter a valid email address."
    if len(password) < 8:
        errors["password"] = "Password must contain at least 8 characters."
    return errors, {"username": username, "email": email, "password": password}


def validate_request(data, partial=False):
    errors, values = {}, {}
    for field in ("title", "description", "request_type", "priority", "status"):
        if partial and field not in data:
            continue
        value = (data.get(field) or "").strip()
        if not value:
            errors[field] = f"{field.replace('_', ' ').title()} is required."
        else:
            values[field] = value
    if "request_type" in values and values["request_type"] not in VALID_TYPES:
        errors["request_type"] = "Choose a valid request type."
    if "priority" in values and values["priority"] not in VALID_PRIORITIES:
        errors["priority"] = "Choose a valid priority."
    if "status" in values and values["status"] not in VALID_STATUSES:
        errors["status"] = "Choose a valid status."
    if not partial or "due_date" in data:
        raw_date = data.get("due_date")
        if raw_date in (None, ""):
            values["due_date"] = None
        else:
            try:
                values["due_date"] = date.fromisoformat(raw_date)
            except (TypeError, ValueError):
                errors["due_date"] = "Enter a valid due date."
    return errors, values


def validate_note(data):
    content = (data.get("content") or "").strip()
    if not content:
        return {"content": "A note cannot be blank."}, None
    if len(content) > 2000:
        return {"content": "A note must be 2,000 characters or fewer."}, None
    return {}, content
