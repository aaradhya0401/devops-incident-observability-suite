
import os
import logging
from datetime import datetime, timezone
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

# OpenTelemetry Tracing Configuration

resource = Resource.create({
    "service.name": "incident-management"
})

tracer_provider = TracerProvider(resource=resource)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://jaeger:4318/v1/traces"
)

span_processor = BatchSpanProcessor(otlp_exporter)

tracer_provider.add_span_processor(span_processor)

trace.set_tracer_provider(tracer_provider)

FlaskInstrumentor().instrument_app(app)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "dev-secret-change-before-deployment"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///incidents.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("incident-management")

# --------------------------------------------------
# PROMETHEUS METRICS
# --------------------------------------------------

REQUEST_COUNT = Counter(
    "incident_app_requests_total",
    "Total number of application requests",
    ["method", "endpoint"]
)

INCIDENT_COUNT = Counter(
    "incidents_created_total",
    "Total incidents created"
)

# --------------------------------------------------
# DATABASE MODELS
# --------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="Medium")
    status = db.Column(db.String(30), default="Open")
    assigned_to = db.Column(db.String(80), default="Unassigned")
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------
# REQUEST MONITORING
# --------------------------------------------------

@app.before_request
def track_request():
    endpoint = request.endpoint or "unknown"
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint
    ).inc()


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or len(password) < 8:
            flash("Enter a username and a password of at least 8 characters.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("register"))

        role = "admin" if User.query.count() == 0 else "user"

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        logger.info("New user registered: %s", username)

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            logger.info("User logged in: %s", username)

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
@login_required
def logout():

    username = current_user.username

    logout_user()

    logger.info("User logged out: %s", username)

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    total = Incident.query.count()

    open_count = Incident.query.filter_by(
        status="Open"
    ).count()

    progress_count = Incident.query.filter_by(
        status="In Progress"
    ).count()

    resolved_count = Incident.query.filter_by(
        status="Resolved"
    ).count()

    return render_template(
        "dashboard.html",
        incidents=incidents,
        total=total,
        open_count=open_count,
        progress_count=progress_count,
        resolved_count=resolved_count
    )


# --------------------------------------------------
# CREATE INCIDENT
# --------------------------------------------------

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_incident():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")

        if not title or not description:
            flash("Please complete all required fields.")
            return redirect(url_for("create_incident"))

        if priority not in ["Low", "Medium", "High", "Critical"]:
            flash("Invalid priority.")
            return redirect(url_for("create_incident"))

        incident = Incident(
            title=title,
            description=description,
            priority=priority,
            created_by=current_user.username
        )

        db.session.add(incident)
        db.session.commit()

        INCIDENT_COUNT.inc()

        logger.info(
            "Incident %s created by %s",
            incident.id,
            current_user.username
        )

        flash("Incident created successfully!")
        return redirect(url_for("dashboard"))

    return render_template("create.html")


# --------------------------------------------------
# UPDATE INCIDENT
# --------------------------------------------------

@app.route("/update/<int:incident_id>", methods=["GET", "POST"])
@login_required
def update_incident(incident_id):

    incident = db.get_or_404(Incident, incident_id)

    if request.method == "POST":

        if current_user.role != "admin" and incident.created_by != current_user.username:
            flash("You are not authorized to update this incident.")
            return redirect(url_for("dashboard"))

        status = request.form.get("status")
        priority = request.form.get("priority")
        assigned_to = request.form.get("assigned_to", "").strip()

        if status not in ["Open", "In Progress", "Resolved"]:
            flash("Invalid status.")
            return redirect(url_for("dashboard"))

        if priority not in ["Low", "Medium", "High", "Critical"]:
            flash("Invalid priority.")
            return redirect(url_for("dashboard"))

        incident.status = status
        incident.priority = priority

        if current_user.role == "admin" and assigned_to:
            incident.assigned_to = assigned_to

        db.session.commit()

        logger.info(
            "Incident %s updated by %s",
            incident.id,
            current_user.username
        )

        flash("Incident updated successfully!")
        return redirect(url_for("dashboard"))

    return render_template("update.html", incident=incident)


# --------------------------------------------------
# DELETE INCIDENT
# --------------------------------------------------

@app.route("/delete/<int:incident_id>", methods=["POST"])
@login_required
def delete_incident(incident_id):

    if current_user.role != "admin":
        flash("Only administrators can delete incidents.")
        return redirect(url_for("dashboard"))

    incident = db.get_or_404(Incident, incident_id)

    db.session.delete(incident)
    db.session.commit()

    logger.info(
        "Incident %s deleted by %s",
        incident_id,
        current_user.username
    )

    flash("Incident deleted successfully!")
    return redirect(url_for("dashboard"))


# --------------------------------------------------
# PROMETHEUS METRICS ENDPOINT
# --------------------------------------------------

@app.route("/metrics")
def metrics():

    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

with app.app_context():
    db.create_all()


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
