import os

from flask import Flask
from flask_cors import CORS

from .database import SessionLocal, engine, Base
from . import models  # Ensure all models are loaded for create_all()

from .routes.patient_routes import patient_bp
from .routes.therapy_minutes_routes import therapy_bp
from .routes.physician_evaluation_routes import physician_bp
from .routes.idt_routes import idt_bp
from .routes.functional_routes import functional_bp
from .routes.medical_necessity_routes import medical_bp
from .routes.risk_routes import risk_bp
from .routes.integration_routes import integration_bp
from .routes.notification_routes import notification_bp
from .routes.session_routes import session_bp
from .routes.family_routes import family_bp
from .routes.capacity_planning_routes import capacity_planning_bp
from .routes.marketplace_routes import marketplace_bp
from .routes.predictive_alert_routes import predictive_alert_bp
from .routes.therapist_analytics_routes import therapist_analytics_bp
from .routes.therapist_performance_routes import therapist_performance_bp
from .routes.automation_routes import automation_bp
from .routes.hiring_routes import hiring_bp
from .routes.therapist_routes import therapist_bp
from .routes.therapist_mobile_routes import therapist_mobile_bp
from .routes.availability_routes import availability_bp
from .routes.staffing_routes import staffing_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.errorhandler(Exception)
    def handle_exception(e):
        return {"error": str(e)}, 500

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("DATABASE_URL is not set")

    @app.route("/debug/flask")
    def debug_flask():
        db = SessionLocal()
        try:
            from sqlalchemy import text

            result = db.execute(text("SELECT 1"))
            return {"connected": True, "result": [list(row) for row in result]}
        except Exception as e:
            return {"connected": False, "error": str(e)}
        finally:
            db.close()

    # Optional table creation - all models are loaded via models/__init__.py
    if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
        Base.metadata.create_all(bind=engine)

    # Register blueprints
    app.register_blueprint(patient_bp)
    app.register_blueprint(therapy_bp)
    app.register_blueprint(physician_bp)
    app.register_blueprint(idt_bp)
    app.register_blueprint(functional_bp, url_prefix="/functional")
    app.register_blueprint(medical_bp)
    app.register_blueprint(risk_bp, url_prefix="/risk")
    app.register_blueprint(integration_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(capacity_planning_bp)
    app.register_blueprint(marketplace_bp, url_prefix="/marketplace")
    app.register_blueprint(predictive_alert_bp)
    app.register_blueprint(therapist_analytics_bp)
    app.register_blueprint(therapist_performance_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(hiring_bp)
    app.register_blueprint(therapist_bp)
    app.register_blueprint(therapist_mobile_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(staffing_bp)

    return app
