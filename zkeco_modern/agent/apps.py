from django.apps import AppConfig
from pathlib import Path


class AgentConfig(AppConfig):
    name = "agent"
    verbose_name = "Comm Center Agent"
    path = str(Path(__file__).resolve().parent)
    
    def ready(self):
        """Import signals when app is ready."""
        import agent.signals  # noqa
