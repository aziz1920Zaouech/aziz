import socket
import subprocess
import os
import time

def is_mongodb_running(host="localhost", port=27017):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect((host, port))
            return True
        except socket.error:
            return False

def start_mongodb():
    print("Tentative de démarrage de MongoDB...")
    mongod_path = r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"  # À adapter selon ta version
    dbpath = r"C:\data\db"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)

    try:
        subprocess.Popen([mongod_path, "--dbpath", dbpath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
    except Exception as e:
        print(f"Erreur de démarrage MongoDB : {e}")

# --- Lancer la vérification MongoDB ---
if not is_mongodb_running():
    start_mongodb()

# --- Lancer ton app Streamlit ---
subprocess.run(["streamlit", "run", "appmain.py/app_streamlit.py"])
