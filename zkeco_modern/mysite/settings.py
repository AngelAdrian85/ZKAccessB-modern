# Minimal shim so pytest-django (and any code expecting mysite.settings) can import.
# Delegate all configuration to the modern settings module.
from zkeco_config.settings import *  # noqa: F401,F403
