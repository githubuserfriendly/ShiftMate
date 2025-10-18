# Explicitly import blueprints

from .user import user_views
from .index import index_views
from .auth import auth_views
from .admin import setup_admin  # not a blueprint
from .shift_view import shift_views
from .attendance_view import attendance_views
from .report_view import report_views

# List of all blueprints to register in create_app()
views = [
    user_views,
    index_views,
    auth_views,
    shift_views,
    attendance_views,
    report_views
]

# setup_admin will be called separately in create_app()
