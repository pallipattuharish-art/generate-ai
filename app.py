"""
Main application entry point for AI Study Assistant.
Initializes Flask app, registers blueprints, sets up SQLite database,
and renders responsive frontend templates.
"""

import os
from flask import Flask, render_template, jsonify
from config import Config
from database import init_db, get_study_stats
from routes import uploads_bp, study_bp, materials_bp
from ai_service import AIService


def create_app(config_class=Config):
    """Application factory for AI Study Assistant."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config["INSTANCE_PATH"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize SQLite database schema
    init_db(app.config["DATABASE_PATH"])

    # Register API Blueprints
    app.register_blueprint(uploads_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(materials_bp)

    ai_service = AIService()

    # Context processor to inject provider status into all templates
    @app.context_processor
    def inject_provider_status():
        return {
            "ai_status": ai_service.get_provider_status()
        }

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # ==================== Page Routes ====================
    @app.route("/")
    def index():
        """Public Landing Page."""
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        """Student Study Dashboard and Metrics."""
        stats = get_study_stats(app.config["DATABASE_PATH"])
        return render_template("dashboard.html", stats=stats)

    @app.route("/study")
    def study():
        """AI Study Workspace (Summaries, Explanations, Flashcards, Quiz)."""
        return render_template("study.html")

    @app.route("/saved")
    def saved_materials():
        """Saved Study Materials & Notes Library."""
        return render_template("saved_materials.html")

    # ==================== Health & Diagnostics ====================
    @app.route("/health")
    def health():
        """Health check endpoint for service monitoring."""
        status = ai_service.get_provider_status()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "ai_provider": status["provider"],
            "is_demo": status["is_demo"]
        }), 200

    # ==================== Error Handlers ====================
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "success": False,
            "error": f"File is too large. Maximum allowed upload size is {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB."
        }), 413

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("index.html", error_msg="The requested page was not found."), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": "An internal server error occurred. Please try again shortly."
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f" * AI Study Assistant is running at: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug)
