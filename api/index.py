import os
import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from securebank_web.app import app

# Vercel looks for the WSGI application object 'app'
if __name__ == "__main__":
    app.run()
