import subprocess
import sys

subprocess.run([sys.executable, "extract_txt.py"], check=True)
subprocess.run([sys.executable, "txt2tei.py"], check=True)
subprocess.run([sys.executable, "TEIAnalyzer.py"], check=True)
subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"], check=True)