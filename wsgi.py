import os
from dotenv import load_dotenv

load_dotenv()

# Default FLASK_ENV to "production" when unset in wsgi.py
if not os.environ.get("FLASK_ENV"):
    os.environ["FLASK_ENV"] = "production"

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
