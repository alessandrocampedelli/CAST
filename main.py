import subprocess

subprocess.run(["python", "extract_txt.py"], check=True)
subprocess.run(["python", "txt2tei.py"], check=True)
subprocess.run(["python", "TEIAnalyzer.py"], check=True)
subprocess.run(["streamlit", "run", "dashboard.py"], check=True)
