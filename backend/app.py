from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db
from seed_data import seed_database_if_empty
from email_utils import get_email_configuration_status

# Import Route Blueprints
from routes.profile_routes import profile_bp
from routes.protected_routes import protected_bp
from routes.monitor_routes import monitor_bp
from routes.demo_routes import demo_bp
from routes.admin_routes import admin_bp
from routes.security_routes import security_bp

def create_app():
    """Initializes and configures the Flask application."""
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(profile_bp)
    app.register_blueprint(protected_bp)
    app.register_blueprint(monitor_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(security_bp)

    @app.route('/')
    def index():
        return jsonify({
            "name": "Fake Profile & Impersonation Detection API",
            "status": "online",
            "version": "1.0.0",
            "documentation": {
                "check_profile": "POST /api/check-profile",
                "register_user": "POST /api/register-user",
                "monitor_username": "POST /api/monitor-username",
                "protected_users": "GET /api/protected-users",
                "alerts": "GET /api/alerts",
                "demo_profiles": "GET /api/demo-profiles",
                "admin_stats": "GET /api/admin/stats"
            }
        })

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    # Ensure DB is initialized and seeded
    with app.app_context():
        init_db()
        seed_database_if_empty()

    return app

app = create_app()

if __name__ == '__main__':
    print("[SERVER] Starting Fake Profile Detection Engine on http://localhost:5000")
    print(f"[EMAIL CONFIG] {get_email_configuration_status()}", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
