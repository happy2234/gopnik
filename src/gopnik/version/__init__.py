"""Version information for Gopnik components."""

CLI_VERSION = "0.1.0"
WEB_VERSION = "0.1"  # Will be updated by web workflow
DESKTOP_VERSION = "0.1.0"  # Will be updated by desktop workflow
API_VERSION = "v1"

def get_version_info():
    return {
        "cli": CLI_VERSION,
        "web": WEB_VERSION,
        "desktop": DESKTOP_VERSION,
        "api": API_VERSION
    }
