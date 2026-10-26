import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"[STARTING] Student Assessment Tracker starting at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
