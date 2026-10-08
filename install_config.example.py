"""Dana install identity — copy to install_config.py and edit for this instance.

This file is NOT secrets. Put SECRET_KEY, DATABASE_URL, hosts, SMS, and payment
credentials in .env only.

PRODUCT_MODE selects which product profile this instance runs (one per install).
Changing PRODUCT_MODE on an existing database is unsupported — provision a new
empty DB if the product must change.

Optional: point settings at another file with DANA_INSTALL_FILE=/path/to/file.py
"""

# Required — exactly one of: academy | school | control
PRODUCT_MODE = "academy"

# Optional public website/landing for THIS instance (panel/PWA always available)
WEBSITE_ENABLED = False
