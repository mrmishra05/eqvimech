from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../static', static_url_path='/')
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.orders import orders_bp
    from routes.customers import customers_bp
    from routes.products import products_bp
    from routes.dashboard import dashboard_bp
    from routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Serve React app
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        return app.send_static_file('index.html')
    
    return app

