import os
import sys
import time
import socket
import webbrowser
import threading
from dotenv import load_dotenv

# When frozen, load .env from next to the exe if present
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)
    env_path = os.path.join(exe_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
else:
    load_dotenv()

from app import create_app

app = create_app()

def find_available_port(default_port=5000):
    for p in range(default_port, default_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return default_port

def launch_browser(url):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[INFO] Could not open browser automatically: {e}")

if __name__ == "__main__":
    configured_port = int(os.getenv("PORT", 5000))
    port = find_available_port(configured_port)

    url = f"http://127.0.0.1:{port}"
    admin_url = f"{url}/admin/login"

    banner = f"""
========================================================================
   🎓 STUDENT ASSESSMENT TRACKER (STANDALONE DESKTOP SERVER)
========================================================================
   🌐 Student Portal:    {url}
   🔐 Admin Login:       {admin_url}

   🔑 Admin Username:    prince
   🔑 Admin Password:    tarunsirkijai
========================================================================
   📂 Reports Folder:    reports/
   💾 Database:          instance/assessment_tracker.db
========================================================================
   Server is active! Opening browser automatically...
   (To close the server, press Ctrl + C or close this window)
========================================================================
"""
    print(banner)

    # Launch browser in a background thread
    threading.Thread(target=launch_browser, args=(url,), daemon=True).start()

    # Run Flask without debug reloader to ensure single stable process
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
