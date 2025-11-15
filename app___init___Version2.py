# near other imports
from .emergency_routes import bp as emergency_bp
from .forum_routes import bp as forum_bp

def create_app(...):
    app = Flask(__name__)
    # existing setup...
    app.register_blueprint(emergency_bp)
    app.register_blueprint(forum_bp)
    return app