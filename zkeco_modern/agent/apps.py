from django.apps import AppConfig


class AgentConfig(AppConfig):
    name = "agent"
    verbose_name = "Comm Center Agent"
    
    def ready(self):
        """Import signals when app is ready."""
        import agent.signals  # noqa
