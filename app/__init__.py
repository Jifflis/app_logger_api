from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Allow only your Next.js app running on localhost:3000
    CORS(app, resources={r"/*": {"origins": "https://www.id-makers.com"}}, supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints
    from app.routes.users import user_bp
    from app.routes.projects import project_bp
    from app.routes.devices import device_bp
    from app.routes.device_logs import log_bp
    from app.routes.device_tags import tag_bp
    from app.routes.tokens import token_bp
    from app.routes.webhook import webhook_bp
    from app.routes.log_tags import log_tag_bp
    from app.routes.actions import actions_bp
    from app.routes.sessions import sessions_bp

    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(webhook_bp)
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(log_bp, url_prefix='/api/logs')
    app.register_blueprint(tag_bp, url_prefix='/api/tags')
    app.register_blueprint(token_bp, url_prefix='/api/tokens')
    app.register_blueprint(log_tag_bp, url_prefix='/api/log_tags')
    app.register_blueprint(actions_bp, url_prefix='/api/actions')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')

    return app
