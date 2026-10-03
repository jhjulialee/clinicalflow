import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from server.extensions import db, migrate
from server.routes import api


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url or f"sqlite:///{instance_path / 'clinicalflow.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    allowed_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
    CORS(app, supports_credentials=True, origins=[allowed_origin])
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Route not found."}), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred."}), 500

    @app.cli.command("seed")
    def seed():
        from datetime import date
        from server.models import DataRequest, RequestNote, User
        db.drop_all()
        db.create_all()
        user = User(username="demoanalyst", email="demo@clinicalflow.local")
        user.set_password("clinicalflow")
        db.session.add(user)
        db.session.flush()
        records = [
            DataRequest(title="Monthly enrollment report", description="Create a fictional monthly enrollment summary for a study leadership meeting.", request_type="Report", priority="High", status="In Progress", due_date=date(2026, 10, 10), owner=user),
            DataRequest(title="Missing laboratory values review", description="Review a synthetic data-quality extract for missing laboratory values and document proposed follow-up.", request_type="Data Quality", priority="Urgent", status="New", due_date=date(2026, 10, 6), owner=user),
            DataRequest(title="Recruitment dashboard refresh", description="Update the fictional recruitment dashboard requirements for an operations review.", request_type="Dashboard", priority="Medium", status="Blocked", due_date=date(2026, 10, 14), owner=user),
        ]
        db.session.add_all(records)
        db.session.flush()
        db.session.add(RequestNote(content="Requirements confirmed. Draft report is in progress.", data_request=records[0], owner=user))
        db.session.commit()
        print("Seeded ClinicalFlow with fictional data. Demo login: demo@clinicalflow.local / clinicalflow")

    return app
