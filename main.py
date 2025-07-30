import subprocess

# Step 1: Esegui estrazione_txt.py
print(" Avvio estrazione_txt.py...")
subprocess.run(["python", "estrazione_txt.py"], check=True)

# Step 2: Esegui txt2tei.py
print(" Avvio txt2tei.py...")
subprocess.run(["python", "txt2tei.py"], check=True)
