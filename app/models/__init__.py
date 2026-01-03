from app.core.database import Base

# Import models to register them with the Base metadata
from .user import User  # noqa: F401
from .device import Device  # noqa: F401
from .browsing_history import BrowsingHistory  # noqa: F401
from .blocked_site import BlockedSite  # noqa: F401
from .activity_log import ActivityLog  # noqa: F401
from .admin_action import AdminAction  # noqa: F401
from .ai_insight import AIInsight  # noqa: F401
from .consent import Consent  # noqa: F401  # noqa: F401

