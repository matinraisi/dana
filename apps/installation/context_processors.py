from .utils import get_installation_config


def installation(request):
    """
    Injects the global InstallationConfig singleton into template contexts as .
    """
    return {
        'installation': get_installation_config(),
    }
