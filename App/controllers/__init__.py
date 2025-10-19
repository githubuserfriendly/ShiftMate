from .user import *
from .auth import *
from App.controllers import initialize
from .attendance_controller import *
from .shift_controller import *
from .report_controller import *

# JWT setup & auth context
from .auth import setup_jwt, add_auth_context

from App.database import db
from .user import create_user

def initialize():
    """
    Dev-only: reset DB and create a couple users.
    Call from a CLI command or a protected admin endpoint.
    """
    db.drop_all()
    db.create_all()
    create_user('bob', 'bobpass', isAdmin=True)
    create_user('rob', 'robpass', isAdmin=False)
