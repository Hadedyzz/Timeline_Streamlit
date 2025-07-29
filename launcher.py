import subprocess
import os
import sys
import webbrowser

def launch_streamlit_app():
    app_path = os.path.join(os.path.dirname(__file__), "main.py")
    log_path = os.path.join(os.path.dirname(__file__), "streamlit_log.txt")

    with open(log_path, "w") as log:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path],
            stdout=log,
            stderr=log,
            shell=True
        )

    # Force open browser
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    launch_streamlit_app()
