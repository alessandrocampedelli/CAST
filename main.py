import subprocess

subprocess.run(["python", "estrazione_txt.py"], check=True)
subprocess.run(["python", "txt2tei.py"], check=True)
subprocess.run(["python", "TEIAnalyzer.py"], check=True)
