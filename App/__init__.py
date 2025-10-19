from .models import *
from .views import *
from .controllers import *
from .main import *

from flask import Flask
from .extensions import db

def create_app(config_object="App.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)

    # Import models once so they’re registered with SQLAlchemy
    with app.app_context():
        from . import models  

    return app
