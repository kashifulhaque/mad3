"""Entry point for the Flask web server.

The create_app() function builds the Flask app: it loads settings, connects
the database, turns on CORS, attaches the API Blueprint, and creates any
missing tables. Building the app inside a function, called the application
factory pattern, lets celery_worker.py and seed.py create the same app
without starting the web server.

To start the server, run `python app.py`.
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db
from routes import api


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # The Vue dev server runs on a different port, so the browser treats it
    # as a different origin and blocks its requests unless the API allows
    # them. CORS adds the response headers that allow them.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(api)

    # Return JSON instead of Flask's default HTML page for unknown URLs and
    # wrong HTTP methods, so every error matches the {"error": ...} shape.
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    # db.create_all() needs to know which app's database to use. The
    # application context supplies that. Outside a request, you open one
    # yourself with app.app_context().
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)
