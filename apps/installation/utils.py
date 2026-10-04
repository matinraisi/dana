from .models import InstallationConfig


def get_installation_config() -> InstallationConfig:
    """
    Cached or direct retrieval of the physical installation singleton configuration.
    """
    return InstallationConfig.get_solo()
