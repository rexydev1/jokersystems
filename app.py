from flask import Flask, render_template, request, url_for, redirect, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import random
from functools import wraps
import sys

# SMS modülünü bulabilmesi için dizini ekle
sys.path.append(os.path.join(os.getcwd(), 'sms'))
try:
    from sms import SendSms
except ImportError:
    SendSms = None

app = Flask(__name__)
CORS(app) # Tüm kökenlerden gelen isteklere izin ver
app.secret_key = "joker_secret_key_999"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Kontrolü
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Yardımcı Fonksiyonlar
def search_in_folder(folder_name, query, limit=100):
    found = []
    if not os.path.exists(folder_name):
        return found
    
    query = query.lower()
    for filename in os.listdir(folder_name):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder_name, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if query in line.lower():
                            found.append(line.strip())
                            if len(found) >= limit:
                                return found
            except Exception:
                continue
    return found

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Giriş bilgileri: joker / joker
        if username == 'joker' and password == 'joker':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Geçersiz kullanıcı adı veya şifre.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

# --- ADMIN BÖLÜMÜ ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Admin bilgileri: rexycann / rexycann
        if username == 'rexycann' and password == 'rexycann':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_index'))
        else:
            return render_template('admin_login.html', error="Hatalı admin girişi!")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_index():
    return render_template('admin_index.html')

# --- USER BÖLÜMÜ ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/log')
@login_required
def log_page():
    return render_template('search.html', 
                           title="Domain Sorgu", 
                           icon="🌐", 
                           description="Data klasöründeki 2.8 milyardan fazla kayıt arasında arama yapın.",
                           placeholder="Arama terimi girin...",
                           api_endpoint="/api/search/log")

@app.route('/plaka')
@login_required
def plaka_page():
    return render_template('search.html', 
                           title="Plaka Veritabanı", 
                           icon="🚗", 
                           description="Araç plaka bilgilerini sorgulayın.",
                           placeholder="Plaka girin (örn. 34ABC123)...",
                           api_endpoint="/api/search/plaka")

@app.route('/craftrise')
@login_required
def craftrise_page():
    return render_template('search.html', 
                           title="CraftRise Veritabanı", 
                           icon="🎮", 
                           description="CraftRise kullanıcı verileri arasında arama yapın.",
                           placeholder="Kullanıcı adı girin...",
                           api_endpoint="/api/search/craftrise")

# API Endpoints
@app.route('/api/search/log', methods=['POST'])
def api_search_log():
    query = request.json.get('query', '')
    if not query:
        return jsonify({"results": [], "count": 0})
    found_lines = search_in_folder('data', query, limit=1000)
    return jsonify({"results": found_lines, "count": len(found_lines)})

@app.route('/api/search/plaka', methods=['POST'])
def api_search_plaka():
    query = request.json.get('query', '')
    if not query:
        return jsonify({"results": [], "count": 0})
    found_lines = search_in_folder('plaka', query, limit=50)
    return jsonify({"results": found_lines, "count": len(found_lines)})

@app.route('/api/search/craftrise', methods=['POST'])
def api_search_craftrise():
    query = request.json.get('query', '')
    if not query:
        return jsonify({"results": [], "count": 0})
    found_lines = search_in_folder('craftrise', query, limit=50)
    return jsonify({"results": found_lines, "count": len(found_lines)})

@app.route('/discord-lookup')
@login_required
def discord_lookup_page():
    return render_template('search.html', 
                           title="Discord ID Sorgu", 
                           icon="🆔", 
                           description="Discord veritabanında ID sorgusu yapın.",
                           placeholder="Discord ID girin...",
                           api_endpoint="/api/search/discord")

@app.route('/api/search/discord', methods=['POST'])
def api_search_discord():
    import re
    query = request.json.get('query', '')
    if not query:
        return jsonify({"results": [], "count": 0})
    
    found_lines = []
    folder_name = 'discord'
    if os.path.exists(folder_name):
        for filename in os.listdir(folder_name):
            if filename.endswith((".txt", ".sql")):
                filepath = os.path.join(folder_name, filename)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if query in line:
                                # IP ve Gmail bilgilerini çekmeye çalış
                                ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
                                gmail_match = re.search(r'[a-zA-Z0-9._%+-]+@gmail\.com', line, re.I)
                                
                                results = []
                                if ip_match: results.append(f"IP: {ip_match.group()}")
                                if gmail_match: results.append(f"GMAİL: {gmail_match.group()}")
                                
                                if results:
                                    found_lines.append(" | ".join(results))
                                else:
                                    found_lines.append("ID bulundu fakat IP/GMAİL bilgisi yok.")
                except Exception:
                    continue
    
    if not found_lines:
        return jsonify({"results": ["ID bulunamadı"], "count": 0})
        
    return jsonify({"results": found_lines, "count": len(found_lines)})

@app.route('/kimlik-arsivi')
@login_required
def kimlik_arsivi():
    # Kök dizindeki 'kimlik' klasöründeki resimleri listele
    kimlik_dir = os.path.join(os.getcwd(), 'kimlik')
    if not os.path.exists(kimlik_dir):
        os.makedirs(kimlik_dir)
    
    kimlikler = [f for f in os.listdir(kimlik_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('kimlik_arsivi.html', kimlikler=kimlikler)

@app.route('/get-kimlik/<filename>')
@login_required
def get_kimlik(filename):
    return send_from_directory('kimlik', filename)

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/password-generator')
@login_required
def password_gen():
    return render_template('password_generator.html')

@app.route('/simple-tools')
@login_required
def simple_tools():
    return render_template('simple_tools.html')

@app.route('/sms-chaos')
@login_required
def sms_chaos():
    return render_template('sms_chaos.html')

@app.route('/temp-mail')
@login_required
def temp_mail():
    return render_template('temp_mail.html')

@app.route('/api/sms-services')
@login_required
def get_sms_services():
    if not SendSms:
        return jsonify({"error": "SMS module not found"}), 500
    
    services = []
    for attribute in dir(SendSms):
        attribute_value = getattr(SendSms, attribute)
        if callable(attribute_value) and not attribute.startswith('__'):
            services.append(attribute)
    return jsonify(services)

@app.route('/api/sms-send', methods=['POST'])
@login_required
def send_sms_api():
    data = request.json
    phone = data.get('phone')
    service = data.get('service')
    
    if not phone or not service:
        return jsonify({"error": "Missing data"}), 400
        
    if not SendSms:
        return jsonify({"error": "SMS module not found"}), 500

    try:
        sms_instance = SendSms(phone, "")
        method = getattr(sms_instance, service)
        # sytem printlerini console'a basmasın diye dummy bir stream ayarlanabilir ama şimdilik kalsın
        method() 
        return jsonify({"status": "success", "service": service})
    except Exception as e:
        return jsonify({"status": "failed", "service": service, "error": str(e)})

@app.route('/api/tools/ip-lookup', methods=['POST'])
@login_required
def ip_lookup():
    ip = request.json.get('ip')
    if not ip:
        return jsonify({"error": "IP missing"}), 400
    
    api_key = "2a24c5c65771480ba87c37f69236f8b9"
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}"
    try:
        import requests
        r = requests.get(url, timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cc', methods=['GET', 'POST'])
@login_required
def cc_gen():
    cc = None
    error = None
    if request.method == 'POST':
        folder = 'cc'
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.txt')]
            if files:
                try:
                    fpath = os.path.join(folder, random.choice(files))
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.strip() for l in f if l.strip()]
                    if lines:
                        cc = random.choice(lines)
                    else:
                        error = "Selected file is empty."
                except Exception as e:
                    error = f"Read error: {e}"
            else:
                error = "No .txt files found in cc folder."
        else:
            error = "'cc' folder not found."

    return render_template('cc.html', cc=cc, error=error)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    env_file = '.env'
    current_token = ""
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('DISCORD_TOKEN='):
                    current_token = line.split('=', 1)[1].strip()
                    break
    
    if request.method == 'POST':
        new_token = request.form.get('token', '').strip()
        if new_token:
            lines = []
            token_found = False
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('DISCORD_TOKEN='):
                            lines.append(f'DISCORD_TOKEN={new_token}\n')
                            token_found = True
                        else:
                            lines.append(line)
            
            if not token_found:
                lines.append(f'DISCORD_TOKEN={new_token}\n')
                
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return redirect(url_for('settings'))
            
    return render_template('settings.html', token=current_token)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
