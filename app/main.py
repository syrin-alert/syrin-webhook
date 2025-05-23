from flask import Flask
from lib.routes import register_routes
from lib.rabbitmq import declare_queues

def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
    declare_queues()
    register_routes(app)
    return app
