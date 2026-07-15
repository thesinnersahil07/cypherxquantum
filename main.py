import os
import sys
import time
import threading
import logging
import base64
import shutil
import hashlib
from flask import Flask, request, render_template_string
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from cryptography.fernet import Fernet, InvalidToken

# ====================================================
# 1. SYSTEM CONFIGURATION & THREAD-SAFE RAM STATE
# ====================================================
TIME_THRESHOLD = 2.0  

state_lock = threading.Lock()
failed_fast = 0
troll_level = 0
data_wiped = False
last_attempt = time.time()
current_target_file = None  # System ab automatically isko track karega!

# ====================================================
# 2. CRYPTOGRAPHY ENGINE
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

def generate_key(password, q_salt):
    fused_password = f"{password}_QUANTUM_{q_salt}"
    digest = hashlib.sha256(fused_password.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_file(raw_data, original_filename, password):
    q_salt = get_quantum_salt()
    payload = original_filename.encode('utf-8') + b'|||' + raw_data
    f = Fernet(generate_key(password, q_salt))
    ciphertext = f.encrypt(payload)
    return q_salt.encode('utf-8') + b'::Q_SALT::' + ciphertext

# ====================================================
# 3. KHTARNAAK 3D WEB UI 
# ====================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cipher X Quantum</title>
    <style>
        body { background-color: #050505; color: #00ffcc; font-family: 'Courier New', monospace; text-align: center; overflow-x: hidden; margin: 0; padding-top: 30px; }
        .scene { perspective: 1200px; margin-top: 2vh; }
        .card { background: rgba(10, 10, 10, 0.9); border: 2px solid #00ffcc; box-shadow: 0 0 30px #00ffcc, inset 0 0 20px #00ffcc; transform: rotateX(10deg); transition: transform 0.6s ease-out, box-shadow 0.6s; padding: 40px; width: 60%; max-width: 700px; margin: auto; border-radius: 15px; }
        .card:hover { transform: rotateX(0deg) scale(1.02); box-shadow: 0 0 50px #00ffcc, inset 0 0 30px #00ffcc; }
        h1 { text-shadow: 0 0 15px #00ffcc; font-size: 2.2em; margin-bottom: 5px;}
        p { color: #888; font-size: 1.1em; margin-bottom: 20px; }
        hr { border-color: rgba(0, 255, 204, 0.3); margin: 30px 0; }
        input[type="file"] { background: #222; color: #00ffcc; border: 1px solid #00ffcc; padding: 8px; margin-bottom: 15px; width: 60%; cursor: pointer;}
        input[type="password"] { padding: 12px; background: #111; color: #00ffcc; border: 1px solid #00ffcc; text-align: center; font-size: 16px; width: 60%; margin-bottom: 15px; }
        input[type="submit"] { padding: 12px 30px; background: #00ffcc; color: black; font-weight: bold; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; box-shadow: 0 0 15px #00ffcc; transition: 0.3s; }
        input[type="submit"]:hover { background: #fff; box-shadow: 0 0 25px #fff; }
        .dl-btn { display: inline-block; margin-top: 20px; padding: 15px 30px; background: transparent; color: #00ffcc; border: 2px solid #00ffcc; font-weight: bold; text-decoration: none; border-radius: 5px; transition: 0.3s; }
        .dl-btn:hover { background: #00ffcc; color: #000; box-shadow: 0 0 20px #00ffcc; }
        .msg-box { margin-top: 30px; padding: 20px; background: rgba(20, 0, 0, 0.8); border: 1px solid #ff0055; color: #ff0055; text-shadow: 0 0 5px #ff0055; font-size: 1.2em; display: inline-block; width: 80%; border-radius: 10px; text-align: left; }
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
            <p>TRUE AES-128 ENCRYPTION & PORTABILITY</p>
            
            <form action="/encrypt" method="POST" enctype="multipart/form-data">
                <input type="file" name="raw_file" required><br>
                <input type="password" name="lock_password" placeholder="Set Password to Lock" required><br>
                <input type="submit" value="🔒 ENCRYPT & LOCK" style="padding: 8px 15px; font-size: 14px;">
            </form>
            <hr>
            <h2 style="color: #fff; text-shadow: 0 0 10px #fff; font-size: 1.5em;">🔓 UNLOCK VAULT 🔓</h2>
            <form action="/decrypt" method="POST" enctype="multipart/form-data">
                <input type="file" name="encrypted_file" required><br>
                <input type="password" name="password" placeholder="Enter Vault Password" required><br>
                <input type="submit" value="DECRYPT & VIEW">
            </form>
        </div>
    </div>
    {% if msg %}
        <div class="msg-box {% if 'GRANTED' in msg or 'SECURED' in msg %}success-box{% elif 'SABKY NIKLYGY' in msg or 'TEEN PAANCH' in msg %}troll-box{% endif %}">
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

@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    file = request.files['raw_file']
    lock_password = request.form.get('lock_password')
    
    if file and lock_password:
        original_filename = file.filename
        raw_data = file.read()
        
        encrypted_payload = encrypt_file(raw_data, original_filename, lock_password)
        b64_payload = base64.b64encode(encrypted_payload).decode('utf-8')
        
        safe_name = original_filename.replace(' ', '_')
        out_name = f"locked_{safe_name}.bin"
        download_btn = f'<br><a href="data:application/octet-stream;base64,{b64_payload}" download="{out_name}" class="dl-btn">📥 DOWNLOAD ENCRYPTED VAULT</a>'
        
        return render_template_string(HTML_TEMPLATE, msg=f"[STATUS] '{original_filename}' SECURELY ENCRYPTED 😎<br>{download_btn}")
    return render_template_string(HTML_TEMPLATE, msg="[ERROR] ENCRYPTION FAILED.")

@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    global failed_fast, troll_level, data_wiped, last_attempt, current_target_file
    enc_file = request.files['encrypted_file']
    password = request.form.get('password', '')
    
    if enc_file:
        with state_lock:
            # Web upload ko temp location mein save karke track karo
            web_filename = "web_target.bin"
            enc_file.save(web_filename)
            if current_target_file != web_filename:
                current_target_file = web_filename
                failed_fast = 0
                troll_level = 0
                data_wiped = False
                last_attempt = time.time()
            
    response_msg, wipe_status = evaluate_defense(password, is_web=True)
    return render_template_string(HTML_TEMPLATE, msg=response_msg)

# ====================================================
# 4. DYNAMIC DECRYPTION & WIPE ENGINE 
# ====================================================
def evaluate_defense(input_pass, is_web=False):
    global failed_fast, troll_level, data_wiped, last_attempt, current_target_file
    
    with state_lock:
        if data_wiped:
            return "[ERROR 404] Data nahi hai yahan. Ghar jao.", True

        # Check if we have an actual file being attacked
        if current_target_file and os.path.exists(current_target_file):
            try:
                with open(current_target_file, "rb") as f:
                    file_data = f.read()
                
                salt_bytes, ciphertext = file_data.split(b'::Q_SALT::', 1)
                q_salt = salt_bytes.decode('utf-8')
                
                fernet_obj = Fernet(generate_key(input_pass, q_salt))
                decrypted_payload = fernet_obj.decrypt(ciphertext)
                
                filename_bytes, raw_data = decrypted_payload.split(b'|||', 1)
                original_filename = filename_bytes.decode('utf-8')
                file_ext = os.path.splitext(original_filename)[1].lower()
                
                failed_fast = 0
                troll_level = 0
                content_html = ""
                
                if is_web:
                    b64_raw = base64.b64encode(raw_data).decode('utf-8')
                    mime = "application/octet-stream"
                    
                    if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                        mime = f"image/{file_ext[1:]}" if file_ext != '.png' else "image/png"
                        content_html = f'<br><img src="data:{mime};base64,{b64_raw}" class="rendered-media">'
                    elif file_ext in ['.mp4', '.webm', '.ogg']:
                        mime = f"video/{file_ext[1:]}"
                        content_html = f'<br><video controls class="rendered-media"><source src="data:{mime};base64,{b64_raw}"></video>'
                    elif file_ext in ['.mp3', '.wav']:
                        mime = f"audio/{file_ext[1:]}"
                        content_html = f'<br><audio controls class="rendered-media"><source src="data:{mime};base64,{b64_raw}"></audio>'
                    elif file_ext == '.pdf':
                        mime = "application/pdf"
                        content_html = f'<br><embed src="data:{mime};base64,{b64_raw}" width="100%" height="400px" class="rendered-media">'
                    else:
                        try:
                            content_html = f'<div class="rendered-text">{raw_data.decode("utf-8")}</div>'
                            mime = "text/plain"
                        except UnicodeDecodeError:
                            content_html = f'<div class="rendered-text" style="color:#00ffcc;">[SECURE BINARY VAULT]<br>File: {original_filename}</div>'
                            
                    out_name = f"decrypted_{original_filename}"
                    dl_button = f'<br><br><a href="data:{mime};base64,{b64_raw}" download="{out_name}" class="dl-btn">📥 DOWNLOAD DECRYPTED FILE</a>'
                    return f"[ACCESS GRANTED] Unlocked: {original_filename}<br>Quantum Salt Used: {q_salt}<br>{content_html}{dl_button}", False

                else:
                    out_name = f"decrypted_{original_filename}"
                    with open(out_name, "wb") as f:
                        f.write(raw_data)
                    return f"[ACCESS GRANTED] Unlocked: {original_filename}\n[SUCCESS] File saved locally as: \033[93m{out_name}\033[0m\nQuantum Salt Used: {q_salt}", False
                    
            except (InvalidToken, ValueError):
                pass # GALAT PASSWORD -> Trap defense activated
            except Exception as e:
                return f"[SYSTEM ERROR] {str(e)}", False
        else:
            return "[WARNING] No active file target detected.", False

        # === 🚨 STAGE 3: BRUTAL WIPE (DELETES THE ACTUAL FILE) 🚨 ===
        if troll_level == 2:
            data_wiped = True
            if current_target_file and os.path.exists(current_target_file):
                try:
                    # Asli file ko kachre se overwrite karke uda dena!
                    with open(current_target_file, "wb") as f:
                        f.write(b"0xDEADBEEF" * 100) 
                    os.remove(current_target_file)
                except:
                    pass
                current_target_file = None # Reset kar do
            return "JAO TAB KARO TEEN PAANCH TUMLOG HUM UDA DIYE DATA", True

        # === STAGE 2: Second Strike ===
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
# 5. MAIN TERMINAL EXECUTION
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
                print("  /encrypt <path>  : Encrypt a file (Creates locked_file.bin)")
                print("  /decrypt <path>  : Decrypt a file (Creates decrypted_file)")
                print("  /help            : Show this menu")
                print("  /exit            : Terminate terminal")
                print("\033[0m")
                continue
                
            # COMMAND: ENCRYPT
            if user_input.lower().startswith("/encrypt "):
                filepath = user_input.split(" ", 1)[1].strip().strip('"').strip("'")
                if os.path.exists(filepath):
                    lock_pass = input("\033[93mSet Custom Password to Lock: \033[0m").strip()
                    try:
                        original_filename = os.path.basename(filepath)
                        with open(filepath, "rb") as orig_file:
                            raw_data = orig_file.read()
                        
                        encrypted_payload = encrypt_file(raw_data, original_filename, lock_pass)
                        
                        out_name = f"locked_{original_filename}.bin"
                        with open(out_name, "wb") as f:
                            f.write(encrypted_payload)
                            
                        print(f"\033[92m\n[SUCCESS] File encrypted and saved locally as '{out_name}' 😎\033[0m\n")
                    except Exception as e:
                        print(f"\033[91m\n[ERROR] {str(e)}\033[0m\n")
                else:
                    print("\033[91m\n[ERROR] File not found!\033[0m\n")
                continue
                
            # COMMAND: DECRYPT (Ab koi separate target zaroori nahi)
            if user_input.lower().startswith("/decrypt "):
                filepath = user_input.split(" ", 1)[1].strip().strip('"').strip("'")
                if os.path.exists(filepath):
                    with state_lock:
                        # Sirf target set karo (copy mat karo) aur naye attack ke liye reset karo
                        if current_target_file != filepath:
                            current_target_file = filepath 
                            failed_fast = 0
                            troll_level = 0
                            data_wiped = False
                            last_attempt = time.time()
                    
                    try:
                        unlock_pass = input("\033[93mEnter Password to Unlock: \033[0m").strip()
                    except EOFError:
                        break # Handles pipeline input ending gracefully
                        
                    response, is_wiped = evaluate_defense(unlock_pass, is_web=False)
                    
                    if "GRANTED" in response:
                        print(f"\033[96m{response}\033[0m\n") 
                    elif "DENIED" in response:
                        print(f"\033[91m{response}\033[0m\n") 
                    else:
                        print(f"\033[93m>>> {response} <<<\033[0m\n") 
                else:
                    print("\033[91m\n[ERROR] File not found!\033[0m\n")
                continue

            # DEFAULT: Agar bina command ke random input aaye (e.g., pipeline se password aayein)
            response, is_wiped = evaluate_defense(user_input, is_web=False)
            
            if "GRANTED" in response:
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