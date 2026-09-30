"""
UPI Payment Gateway for Trading Vault
Flask-based payment system with UPI QR code generation, UTR submission, and Discord bot integration
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import json
import os
import qrcode
import io
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import random
import string
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
app.config['JSON_AS_ASCII'] = False

# Web authentication credentials
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "admin")

# Database setup
DB_FILE = "payments.db"

# UPI Configuration
UPI_ID = os.getenv("UPI_ID", "yourname@upi")
UPI_NAME = os.getenv("UPI_NAME", "Trading Vault")
UPI_MERCHANT_CODE = os.getenv("UPI_MERCHANT_CODE", "")

# Discord Configuration
DISCORD_BOT_WEBHOOK = os.getenv("DISCORD_BOT_WEBHOOK", "")
PAYMENT_TIMEOUT_MINUTES = int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "10"))

# Verifier role ID for Discord notifications
VERIFIER_ROLE_ID = os.getenv("VERIFIER_ROLE_ID", "")

def init_db():
    """Initialize the payments database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE NOT NULL,
            order_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            status TEXT DEFAULT 'pending',
            upi_transaction_id TEXT,
            utr_number TEXT,
            screenshot_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            utr_submitted_at TIMESTAMP,
            verified_at TIMESTAMP,
            verified_by INTEGER,
            notes TEXT
        )
    ''')
    
    # Create payment settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upi_id TEXT NOT NULL,
            upi_name TEXT NOT NULL,
            merchant_code TEXT,
            min_amount REAL DEFAULT 1,
            max_amount REAL DEFAULT 100000,
            auto_verify BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default settings if not exists
    cursor.execute('SELECT COUNT(*) FROM payment_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO payment_settings (upi_id, upi_name, merchant_code, min_amount, max_amount, auto_verify)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (UPI_ID, UPI_NAME, UPI_MERCHANT_CODE, 1, 100000, 0))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_payment_id():
    """Generate unique payment ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PAY{timestamp}{random_str}"

def generate_upi_link(amount, payment_id, note="Trading Vault"):
    """Generate UPI payment link"""
    # UPI link format: upi://pay?pa=upi_id&pn=name&am=amount&tr=transaction_id&tn=note
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount}&tr={payment_id}&tn={note}"
    return upi_link

def generate_qr_code(upi_link):
    """Generate QR code for UPI payment"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.read()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def send_discord_notification(payment_data):
    """Send Discord notification to verifier role"""
    if not DISCORD_BOT_WEBHOOK:
        print("Discord webhook not configured")
        return False
    
    try:
        embed = {
            "title": "💳 New Payment Submitted for Verification",
            "description": f"A new payment requires your verification",
            "color": 5814783,  # Blue color
            "fields": [
                {
                    "name": "Payment ID",
                    "value": payment_data['payment_id'],
                    "inline": True
                },
                {
                    "name": "Order ID",
                    "value": payment_data['order_id'],
                    "inline": True
                },
                {
                    "name": "User",
                    "value": f"{payment_data['user_name']} (ID: {payment_data['user_id']})",
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"₹{payment_data['amount']}",
                    "inline": True
                },
                {
                    "name": "UTR Number",
                    "value": payment_data.get('utr_number', 'Not provided'),
                    "inline": True
                },
                {
                    "name": "Expires At",
                    "value": payment_data.get('expires_at', 'N/A'),
                    "inline": True
                },
                {
                    "name": "Payment Link",
                    "value": f"{os.getenv('PAYMENT_GATEWAY_URL', 'http://localhost:5001')}/payment/{payment_data['payment_id']}",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Trading Vault Payment Gateway"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        data = {
            "embeds": [embed]
        }
        
        if VERIFIER_ROLE_ID:
            data["content"] = f"<@&{VERIFIER_ROLE_ID}> New payment requires verification!"
        
        response = requests.post(DISCORD_BOT_WEBHOOK, json=data, timeout=10)
        
        if response.status_code == 204:
            print("Discord notification sent successfully")
            return True
        else:
            print(f"Failed to send Discord notification: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False

# Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for payment gateway"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == WEB_USERNAME and password == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout from payment gateway"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Main dashboard for payment management"""
    conn = get_db_connection()
    
    # Get payment statistics
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM payments')
    total_payments = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
    pending_payments = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "verified"')
    verified_payments = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM payments WHERE status = "verified"')
    total_revenue = cursor.fetchone()[0] or 0
    
    # Get recent payments
    cursor.execute('''
        SELECT * FROM payments 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    recent_payments = cursor.fetchall()
    
    # Get payment settings
    cursor.execute('SELECT * FROM payment_settings ORDER BY id DESC LIMIT 1')
    settings = cursor.fetchone()
    
    conn.close()
    
    return render_template('payment_dashboard.html',
                          total_payments=total_payments,
                          pending_payments=pending_payments,
                          verified_payments=verified_payments,
                          total_revenue=total_revenue,
                          recent_payments=recent_payments,
                          settings=settings)

@app.route('/api/create_payment', methods=['POST'])
def create_payment():
    """Create a new payment"""
    try:
        data = request.json
        
        order_id = data.get('order_id')
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        amount = float(data.get('amount'))
        currency = data.get('currency', 'INR')
        notes = data.get('notes', '')
        
        # Validate amount
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT min_amount, max_amount FROM payment_settings ORDER BY id DESC LIMIT 1')
        settings = cursor.fetchone()
        
        if settings:
            min_amount = settings['min_amount']
            max_amount = settings['max_amount']
            
            if amount < min_amount or amount > max_amount:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': f'Amount must be between {min_amount} and {max_amount}'
                })
        
        # Generate payment ID
        payment_id = generate_payment_id()
        
        # Calculate expiration time
        expires_at = datetime.now() + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)
        
        # Generate UPI link and QR code
        note = f"Trading Vault - {order_id}"
        upi_link = generate_upi_link(amount, payment_id, note)
        qr_code = generate_qr_code(upi_link)
        
        # Insert payment into database
        cursor.execute('''
            INSERT INTO payments (payment_id, order_id, user_id, user_name, amount, currency, notes, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (payment_id, order_id, user_id, user_name, amount, currency, notes, expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'upi_link': upi_link,
            'qr_code': qr_code,
            'amount': amount,
            'currency': currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments():
    """Get all payments with optional filtering"""
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM payments'
        params = []
        
        if status_filter:
            query += ' WHERE status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        payments = cursor.fetchall()
        
        # Convert to list of dicts
        payments_list = [dict(payment) for payment in payments]
        
        conn.close()
        
        return jsonify({'success': True, 'payments': payments_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/payment/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get specific payment details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        conn.close()
        
        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'})
        
        payment_dict = dict(payment)
        
        # Check if payment is expired
        if payment_dict['status'] == 'pending' and payment_dict.get('expires_at'):
            expires_at = datetime.fromisoformat(payment_dict['expires_at'])
            if datetime.now() > expires_at:
                # Update status to expired
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE payments SET status = ? WHERE payment_id = ?', ('expired', payment_id))
                conn.commit()
                conn.close()
                payment_dict['status'] = 'expired'
        
        return jsonify({'success': True, 'payment': payment_dict})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/submit_utr', methods=['POST'])
def submit_utr():
    """Submit UTR number for payment verification"""
    try:
        data = request.json
        payment_id = data.get('payment_id')
        utr_number = data.get('utr_number')
        
        if not payment_id or not utr_number:
            return jsonify({'success': False, 'error': 'Payment ID and UTR number are required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if payment exists and is pending
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            conn.close()
            return jsonify({'success': False, 'error': 'Payment not found'})
        
        if payment['status'] != 'pending':
            conn.close()
            return jsonify({'success': False, 'error': f'Payment is {payment["status"]}, cannot submit UTR'})
        
        # Check if payment is expired
        if payment.get('expires_at'):
            expires_at = datetime.fromisoformat(payment['expires_at'])
            if datetime.now() > expires_at:
                conn.close()
                return jsonify({'success': False, 'error': 'Payment has expired'})
        
        # Update payment with UTR number
        cursor.execute('''
            UPDATE payments 
            SET utr_number = ?,
                utr_submitted_at = CURRENT_TIMESTAMP,
                status = 'awaiting_verification'
            WHERE payment_id = ?
        ''', (utr_number, payment_id))
        
        conn.commit()
        
        # Get updated payment data
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        updated_payment = cursor.fetchone()
        
        conn.close()
        
        # Send Discord notification
        send_discord_notification(dict(updated_payment))
        
        return jsonify({
            'success': True,
            'message': 'UTR submitted successfully. Payment is now awaiting verification.',
            'payment': dict(updated_payment)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/verify_payment', methods=['POST'])
@login_required
def verify_payment():
    """Verify a payment"""
    try:
        data = request.json
        payment_id = data.get('payment_id')
        upi_transaction_id = data.get('upi_transaction_id')
        verified_by = data.get('verified_by')
        notes = data.get('notes', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if payment exists
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            conn.close()
            return jsonify({'success': False, 'error': 'Payment not found'})
        
        if payment['status'] == 'verified':
            conn.close()
            return jsonify({'success': False, 'error': 'Payment already verified'})
        
        # Update payment status
        cursor.execute('''
            UPDATE payments 
            SET status = 'verified',
                upi_transaction_id = ?,
                verified_at = CURRENT_TIMESTAMP,
                verified_by = ?,
                notes = ?
            WHERE payment_id = ?
        ''', (upi_transaction_id, verified_by, notes, payment_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Payment verified successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reject_payment', methods=['POST'])
@login_required
def reject_payment():
    """Reject a payment"""
    try:
        data = request.json
        payment_id = data.get('payment_id')
        notes = data.get('notes', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if payment exists
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            conn.close()
            return jsonify({'success': False, 'error': 'Payment not found'})
        
        if payment['status'] == 'verified':
            conn.close()
            return jsonify({'success': False, 'error': 'Cannot reject verified payment'})
        
        # Update payment status
        cursor.execute('''
            UPDATE payments 
            SET status = 'rejected',
                notes = ?
            WHERE payment_id = ?
        ''', (notes, payment_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Payment rejected successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def payment_settings():
    """Get or update payment settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM payment_settings ORDER BY id DESC LIMIT 1')
        settings = cursor.fetchone()
        conn.close()
        
        if settings:
            return jsonify({'success': True, 'settings': dict(settings)})
        else:
            return jsonify({'success': False, 'error': 'Settings not found'})
    
    elif request.method == 'POST':
        data = request.json
        
        cursor.execute('''
            UPDATE payment_settings 
            SET upi_id = ?, upi_name = ?, merchant_code = ?, 
                min_amount = ?, max_amount = ?, auto_verify = ?
            WHERE id = (SELECT id FROM payment_settings ORDER BY id DESC LIMIT 1)
        ''', (
            data.get('upi_id'),
            data.get('upi_name'),
            data.get('merchant_code'),
            data.get('min_amount'),
            data.get('max_amount'),
            data.get('auto_verify', False)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})

@app.route('/payment/<payment_id>')
def payment_page(payment_id):
    """Public payment page for users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()
    
    cursor.execute('SELECT * FROM payment_settings ORDER BY id DESC LIMIT 1')
    settings = cursor.fetchone()
    
    conn.close()
    
    if not payment:
        return render_template('error.html', message='Payment not found')
    
    # Generate UPI link and QR code if payment is pending
    qr_code = None
    upi_link = None
    
    if payment['status'] == 'pending':
        note = f"Trading Vault - {payment['order_id']}"
        upi_link = generate_upi_link(payment['amount'], payment_id, note)
        qr_code = generate_qr_code(upi_link)
    
    return render_template('payment_page.html',
                          payment=dict(payment),
                          settings=dict(settings) if settings else None,
                          qr_code=qr_code,
                          upi_link=upi_link)

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
