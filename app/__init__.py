from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)

    # Register blueprints
    from app.routes.users import user_bp
    from app.routes.projects import project_bp
    from app.routes.devices import device_bp
    from app.routes.device_logs import log_bp
    from app.routes.device_tags import tag_bp
    from app.routes.tokens import token_bp

    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(log_bp, url_prefix='/api/logs')
    app.register_blueprint(tag_bp, url_prefix='/api/tags')
    app.register_blueprint(token_bp, url_prefix='/api/tokens')

    return app
