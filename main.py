import os
import sys
import time
import threading
import logging
import base64
import shutil
from flask import Flask, request, render_template_string
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# ====================================================
# 1. SYSTEM CONFIGURATION & THREAD-SAFE RAM STATE
# ====================================================
DATA_FILE = "secret_data.bin" 
ACTUAL_PASSWORD = "cipherquantum"
TIME_THRESHOLD = 2.0  

state_lock = threading.Lock()
failed_fast = 0
troll_level = 0
data_wiped = False
last_attempt = time.time()
file_ext = ".txt" # NEW: Duniya ki har file track karne ke liye

# ====================================================
# 2. QUANTUM RANDOM NUMBER GENERATOR (QRNG)
# ====================================================
def get_quantum_salt():
    try:
        qc = QuantumCircuit(4, 4)
        qc.h([0, 1, 2, 3]) 
        qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1)
        result = job.result().get_counts()
        return list(result.keys())[0]
    except Exception:
        return "Q-ERROR-FALLBACK-999"

# ====================================================
# 3. KHTARNAAK 3D WEB UI (HTML/CSS)
# ====================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cipher X Quantum</title>
    <style>
        body { background-color: #050505; color: #00ffcc; font-family: 'Courier New', monospace; text-align: center; overflow-x: hidden; margin: 0; padding-top: 30px; }
        .scene { perspective: 1200px; margin-top: 2vh; }
        .card { background: rgba(10, 10, 10, 0.9); border: 2px solid #00ffcc; box-shadow: 0 0 30px #00ffcc, inset 0 0 20px #00ffcc; transform: rotateX(10deg); transition: transform 0.6s ease-out, box-shadow 0.6s; padding: 40px; width: 60%; max-width: 650px; margin: auto; border-radius: 15px; }
        .card:hover { transform: rotateX(0deg) scale(1.02); box-shadow: 0 0 50px #00ffcc, inset 0 0 30px #00ffcc; }
        h1 { text-shadow: 0 0 15px #00ffcc; font-size: 2.2em; margin-bottom: 5px;}
        p { color: #888; font-size: 1.1em; margin-bottom: 20px; }
        hr { border-color: rgba(0, 255, 204, 0.3); margin: 30px 0; }
        .btn { border: 1px solid #00ffcc; color: #00ffcc; background-color: transparent; padding: 10px 20px; font-size: 14px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn:hover { background: #00ffcc; color: #000; box-shadow: 0 0 15px #00ffcc; }
        input[type="file"] { background: #222; color: #00ffcc; border: 1px solid #00ffcc; padding: 5px;}
        input[type="password"] { padding: 12px; background: #111; color: #00ffcc; border: 1px solid #00ffcc; text-align: center; font-size: 16px; width: 60%; margin-bottom: 15px; }
        input[type="submit"] { padding: 12px 30px; background: #00ffcc; color: black; font-weight: bold; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; box-shadow: 0 0 15px #00ffcc; transition: 0.3s; }
        input[type="submit"]:hover { background: #fff; box-shadow: 0 0 25px #fff; }
        .msg-box { margin-top: 30px; padding: 20px; background: rgba(20, 0, 0, 0.8); border: 1px solid #ff0055; color: #ff0055; text-shadow: 0 0 5px #ff0055; font-size: 1.2em; display: inline-block; width: 60%; border-radius: 10px; text-align: left; }
        .success-box { border-color: #00ffcc; color: #00ffcc; text-shadow: 0 0 5px #00ffcc; background: rgba(0, 20, 20, 0.8); }
        .troll-box { border-color: #ffaa00; color: #ffaa00; text-shadow: 0 0 5px #ffaa00; font-size: 1.5em; font-weight: bold;}
        .rendered-media { max-width: 100%; max-height: 400px; border-radius: 8px; margin-top: 15px; border: 2px solid #00ffcc; box-shadow: 0 0 15px #00ffcc; outline: none; }
        .rendered-text { background: #000; padding: 15px; border-radius: 5px; border: 1px solid #00ffcc; overflow-x: auto; white-space: pre-wrap; font-size: 14px;}
    </style>
</head>
<body>
    <div class="scene">
        <div class="card">
            <h1>⚛️ QUANTUM VAULT ⚛️</h1>
            <p>A.I. ENCRYPTION ENGINE ACTIVE</p>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="dataset" required>
                <input type="submit" value="ENGAGE LOCK" style="padding: 8px 15px; font-size: 14px;">
            </form>
            <hr>
            <h2 style="color: #fff; text-shadow: 0 0 10px #fff; font-size: 1.5em;">🔐 ACCESS SECURE DATA 🔐</h2>
            <form action="/view" method="POST">
                <input type="password" name="password" placeholder="Enter Access Key" required><br>
                <input type="submit" value="DECRYPT VAULT">
            </form>
        </div>
    </div>
    {% if msg %}
        <div class="msg-box {% if 'GRANTED' in msg or 'SECURED' in msg or 'ACCEPTED' in msg %}success-box{% elif 'SABKY NIKLYGY' in msg or 'TEEN PAANCH' in msg %}troll-box{% endif %}">
            {{ msg | safe }}
        </div>
    {% endif %}
</body>
</html>
"""

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    global failed_fast, troll_level, data_wiped, last_attempt, file_ext
    file = request.files['dataset']
    if file:
        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1] # Extension nikalna (e.g., .mp4, .pdf)
        
        with state_lock:
            file.save(DATA_FILE)
            failed_fast = 0
            troll_level = 0
            data_wiped = False
            last_attempt = time.time()
        return render_template_string(HTML_TEMPLATE, msg=f"[STATUS] {file_ext.upper()} DATA SECURED & COUNTERS RESET 😎")
    return render_template_string(HTML_TEMPLATE, msg="[ERROR] UPLOAD FAILED.")

@app.route('/view', methods=['POST'])
def view_data():
    password = request.form.get('password', '')
    response_msg, wipe_status = evaluate_defense(password, is_web=True)
    return render_template_string(HTML_TEMPLATE, msg=response_msg)

# ====================================================
# 4. UNIVERSAL CORE DEFENSE ENGINE 
# ====================================================
def evaluate_defense(input_pass, is_web=False):
    global failed_fast, troll_level, data_wiped, last_attempt, file_ext
    
    with state_lock:
        if data_wiped:
            return "[ERROR 404] Data nahi hai yahan. Ghar jao.", True

        # === 🚨 ADMIN OVERRIDE 🚨 ===
        if input_pass == ACTUAL_PASSWORD:
            failed_fast = 0
            troll_level = 0
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "rb") as f:
                        raw_data = f.read()

                    content_html = ""
                    
                    # 1. IMAGE SUPPORT
                    if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                        if is_web:
                            b64 = base64.b64encode(raw_data).decode('utf-8')
                            mime = "image/png" if file_ext == '.png' else f"image/{file_ext[1:]}"
                            content_html = f'<br><img src="data:{mime};base64,{b64}" class="rendered-media">'
                        else:
                            content_html = f"\n\n[IMAGE DETECTED - {file_ext.upper()}]\n>>> Open Web Portal to View <<<"
                    
                    # 2. VIDEO SUPPORT (MP4, WEBM)
                    elif file_ext in ['.mp4', '.webm', '.ogg']:
                        if is_web:
                            b64 = base64.b64encode(raw_data).decode('utf-8')
                            mime = f"video/{file_ext[1:]}"
                            content_html = f'<br><video controls class="rendered-media"><source src="data:{mime};base64,{b64}"></video>'
                        else:
                            content_html = f"\n\n[VIDEO DETECTED - {file_ext.upper()}]\n>>> Open Web Portal to Play <<<"

                    # 3. AUDIO SUPPORT (MP3, WAV)
                    elif file_ext in ['.mp3', '.wav']:
                        if is_web:
                            b64 = base64.b64encode(raw_data).decode('utf-8')
                            mime = "audio/mpeg" if file_ext == '.mp3' else f"audio/{file_ext[1:]}"
                            content_html = f'<br><audio controls class="rendered-media"><source src="data:{mime};base64,{b64}"></audio>'
                        else:
                            content_html = f"\n\n[AUDIO DETECTED - {file_ext.upper()}]\n>>> Open Web Portal to Listen <<<"

                    # 4. PDF SUPPORT
                    elif file_ext == '.pdf':
                        if is_web:
                            b64 = base64.b64encode(raw_data).decode('utf-8')
                            content_html = f'<br><embed src="data:application/pdf;base64,{b64}" width="100%" height="400px" class="rendered-media" type="application/pdf">'
                        else:
                            content_html = "\n\n[PDF DOCUMENT DETECTED]\n>>> Open Web Portal to Read <<<"

                    # 5. TEXT OR UNKNOWN BINARY FALLBACK
                    else:
                        try:
                            # Try to decode as Text
                            text_data = raw_data.decode('utf-8')
                            if is_web:
                                content_html = f'<div class="rendered-text">{text_data}</div>'
                            else:
                                content_html = f"\n\n-- SECRET TEXT DATA --\n{text_data}"
                        except UnicodeDecodeError:
                            # If it's a binary like .zip, .exe, etc.
                            msg = f"[SECURE BINARY VAULT]\nFormat: {file_ext.upper()}\nFile is highly encrypted in RAM. Cannot be previewed in text mode."
                            if is_web:
                                content_html = f'<div class="rendered-text" style="color:#ffaa00;">{msg}</div>'
                            else:
                                content_html = f"\n\n{msg}"
                    
                    if is_web:
                        return f"[ADMIN OVERRIDE ACCEPTED]<br>Quantum Salt: {get_quantum_salt()}<br>{content_html}", False
                    else:
                        return f"[ADMIN OVERRIDE ACCEPTED]\nQuantum Salt: {get_quantum_salt()}{content_html}", False
                except Exception as e:
                    return f"[ERROR] Could not process file data: {str(e)}", False
            else:
                return "[WARNING] No data file found. Please upload via Web Portal or CLI.", False

        # === STAGE 3: Final Strike -> Secure Wipe ===
        if troll_level == 2:
            data_wiped = True
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "wb") as f:
                        f.write(b"0xDEADBEEF" * 100) 
                    os.remove(DATA_FILE)
                except:
                    pass
            return "JAO TAB KARO TEEN PAANCH TUMLOG HUM UDA DIYE DATA", True

        # === STAGE 2: Second Strike Warning ===
        if troll_level == 1:
            troll_level = 2
            return "SAMAJH NAI AARA EK BAAR ME BOL RY TOH UDD JAYEGA SARA DATA TOH THIK LAGEGA FALTU KA HACKER BUDDHI LAGA RA", False

        # === Fast Bot Detection ===
        current_time = time.time()
        time_gap = current_time - last_attempt
        last_attempt = current_time

        if time_gap < TIME_THRESHOLD:
            failed_fast += 1
        else:
            failed_fast = 1 
            
        # === STAGE 1: First Strike ===
        if failed_fast >= 3:
            troll_level = 1
            return "LEVEL SABKY NIKLYGY! Lekin is file ka nahi niklega.", False

        return "[ACCESS DENIED] Wrong Password.", False

def run_web_server():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# ====================================================
# 5. MAIN TERMINAL EXECUTION (CLI UPLOAD)
# ====================================================
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[92m")
    print("="*60)
    print(" ⚛️  CIPHER X QUANTUM - ADVANCED DEFENSE TERMINAL  ⚛️")
    print(" 🌐 3D Web UI Live at: http://127.0.0.1:5000")
    print(" 💡 Type \033[93m/help\033[92m to see available CLI commands.")
    print("="*60 + "\033[0m\n")

    while True:
        try:
            user_input = input("root@quantum-vault:~# ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', '/exit']:
                break
                
            if user_input.lower() == "/help":
                print("\033[93m")
                print("=== SYSTEM COMMANDS ===")
                print("  /upload <path>   : Secure a local file into the Vault")
                print("  /help            : Show this menu")
                print("  /exit            : Terminate terminal")
                print("  <any other text> : Treated as Access Key attempt")
                print("\033[0m")
                continue
                
            if user_input.lower().startswith("/upload "):
                filepath = user_input.split(" ", 1)[1].strip().strip('"').strip("'")
                
                if os.path.exists(filepath):
                    try:
                        filename = filepath.lower()
                        new_ext = os.path.splitext(filename)[1]
                        
                        with state_lock:
                            shutil.copy2(filepath, DATA_FILE)
                            failed_fast = 0
                            troll_level = 0
                            data_wiped = False
                            last_attempt = time.time()
                            file_ext = new_ext # Extension update karna zaroori hai!
                            
                        print(f"\033[92m\n[STATUS] {new_ext.upper()} DATA SECURED VIA CLI & COUNTERS RESET 😎\033[0m\n")
                    except Exception as e:
                        print(f"\033[91m\n[ERROR] Could not secure file: {str(e)}\033[0m\n")
                else:
                    print("\033[91m\n[ERROR] File not found! Please check the path.\033[0m\n")
                continue

            response, is_wiped = evaluate_defense(user_input, is_web=False)
            
            if "ACCEPTED" in response or "GRANTED" in response:
                print(f"\033[96m{response}\033[0m\n") 
            elif "DENIED" in response:
                print(f"\033[91m{response}\033[0m\n") 
            else:
                print(f"\033[93m>>> {response} <<<\033[0m\n") 
                
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n[SYSTEM] Terminating Securely...")
            break