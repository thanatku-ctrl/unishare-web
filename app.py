import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.')
DB_PATH = os.path.join(os.path.dirname(__file__), 'unishare.db')

DEFAULT_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%23cbd5e1'/%3E%3Ccircle cx='50' cy='38' r='18' fill='%23ffffff'/%3E%3Cpath d='M20,84 C20,68 34,60 50,60 C66,60 80,68 80,84 Z' fill='%23ffffff'/%3E%3C/svg%3E"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            faculty TEXT NOT NULL,
            role TEXT NOT NULL,
            avatar TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure is_admin column exists if table was previously created
    cursor.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'is_admin' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    # Ensure juner is always marked as admin in SQLite
    cursor.execute("UPDATE users SET is_admin = 1, role = 'ผู้ดูแลระบบ (Admin) / รุ่นพี่ปี 4' WHERE username = 'juner'")

    # 2. Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            img_url TEXT NOT NULL,
            owner_username TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            owner_role TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Messages Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            sender_avatar TEXT,
            text TEXT NOT NULL,
            type TEXT DEFAULT 'text',
            time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Default Users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            (
                'cheer',
                generate_password_hash('1234'),
                'น้องเชียร์ (วิศวะปัญญาประดิษฐ์)',
                'วิศวะปัญญาประดิษฐ์',
                'นักศึกษา (ผู้ขอเช่า/ยืม)',
                DEFAULT_AVATAR,
                0
            ),
            (
                'juner',
                generate_password_hash('1234'),
                'พี่จูนเนอร์ (ผู้ดูแลระบบ/Admin)',
                'วิศวะปัญญาประดิษฐ์',
                'ผู้ดูแลระบบ (Admin) / รุ่นพี่ปี 4',
                DEFAULT_AVATAR,
                1
            )
        ]
        cursor.executemany('''
            INSERT INTO users (username, password_hash, name, faculty, role, avatar, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_users)
        print("Initialized default users: cheer (student), juner (admin)")

    # Seed Default Products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            (
                'p1',
                'กล้อง Canon EOS 80D + เลนส์ 18-135mm',
                'rent',
                'อุปกรณ์ถ่ายภาพ',
                350,
                'บาท/วัน',
                'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500',
                'juner',
                'พี่จูนเนอร์ (วิศวะปัญญาประดิษฐ์)',
                'รุ่นพี่ปี 4 (วิศวะปัญญาประดิษฐ์)',
                'กล้องสภาพดีมาก เหมาะสำหรับงานส่งอาจารย์หรืองานอีเวนต์ มหาวิทยาลัย มีกระเป๋าและเมมโมรี่การ์ดให้พร้อมใช้งาน'
            ),
            (
                'p2',
                'ชุดครุยรับปริญญา มหาวิทยาลัย (ไซส์ M)',
                'rent',
                'เสื้อผ้า/แต่งกาย',
                250,
                'บาท/วัน',
                'https://images.unsplash.com/photo-1627556704302-624286467c65?w=500',
                'nut',
                'พี่นัท (วิศวะฯ)',
                'ศิษย์เก่า',
                'ชุดครุยเนื้อผ้าอย่างดี ตัดเย็บประณีต สภาพ 90% ซักแห้งพร้อมใช้งาน ถ่ายรูปวันซ้อมใหญ่หรือวันกิจกรรมได้เลย'
            ),
            (
                'p3',
                'หนังสือเรียน CALCULUS 1 สำหรับวิศวะฯ',
                'borrow',
                'หนังสือ/ชีตสรุป',
                0,
                'ยืมฟรี (มัดจำ 100)',
                'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500',
                'got',
                'พี่ก็อต (วิศวะฯ คอม)',
                'รุ่นพี่ปี 3',
                'มีรอยไฮไลท์จุดสำคัญไว้ให้หมดแล้ว เหมาะกับน้องๆ ปี 1 ที่กำลังเตรียมสอบกลางภาค ยืมได้ตลอดเทอม'
            ),
            (
                'p4',
                'โน้ตบุ๊กสำหรับการศึกษา RAM 16GB SSD 512GB',
                'buy',
                'อุปกรณ์การเรียน',
                12500,
                'บาท (ขายขาด)',
                'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500',
                'top',
                'พี่ต๊อบ (บริหารธุรกิจ)',
                'ศิษย์เก่า',
                'ส่งต่อโน้ตบุ๊กสภาพดีมาก ใช้งานพิมพ์งาน สรุปชีต สเปกแรงกำลังดี สภาพ 90% พร้อมกระเป๋าใส่'
            )
        ]
        cursor.executemany('''
            INSERT INTO products (id, title, type, category, price, unit, img_url, owner_username, owner_name, owner_role, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_products)
        print("Initialized default products (p1 - p4)")

    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

# Serve Frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ----------------- Auth API -----------------
# ----------------- Auth API -----------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', '')).strip()
    name = str(data.get('name', '')).strip()
    faculty = str(data.get('faculty', '')).strip()
    role = str(data.get('role', 'นักศึกษา (ผู้ขอเช่า/ยืม/ซื้อ)')).strip()

    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

    if len(password) < 4:
        return jsonify({'success': False, 'message': 'รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร'}), 400

    # Prevent registering with reserved system usernames
    if username in ['juner', 'cheer', 'admin']:
        return jsonify({'success': False, 'message': f'ชื่อผู้ใช้ "{username}" เป็นชื่อสงวนของระบบ'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': f'รหัสนักศึกษา/ชื่อผู้ใช้ "{username}" มีในระบบแล้ว'}), 400

    password_hash = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (username, password_hash, name, faculty, role, avatar, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    ''', (username, password_hash, name, faculty, role, DEFAULT_AVATAR))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    user_info = {
        'id': user_id,
        'username': username,
        'name': name,
        'shortName': name.split(' ')[0],
        'faculty': faculty,
        'role': role,
        'avatar': DEFAULT_AVATAR,
        'isAdmin': False
    }

    return jsonify({'success': True, 'message': 'ลงทะเบียนสำเร็จ!', 'user': user_info})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', '')).strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'กรุณากรอกชื่อผู้ใช้และรหัสผ่าน'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'}), 401

    is_admin = bool(row['is_admin']) if ('is_admin' in row.keys() and row['is_admin']) else (row['username'] == 'juner')

    user_info = {
        'id': row['id'],
        'username': row['username'],
        'name': row['name'],
        'shortName': row['name'].split(' ')[0],
        'faculty': row['faculty'],
        'role': row['role'],
        'avatar': row['avatar'] or DEFAULT_AVATAR,
        'isAdmin': is_admin
    }

    return jsonify({'success': True, 'message': f'ยินดีต้อนรับคุณ {row["name"]}', 'user': user_info})

@app.route('/api/auth/users', methods=['GET'])
def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, faculty, role, is_admin, created_at FROM users ORDER BY id ASC")
    users = []
    for r in cursor.fetchall():
        u = dict(r)
        u['isAdmin'] = bool(u.get('is_admin', 0)) or (u.get('username') == 'juner')
        users.append(u)
    conn.close()
    return jsonify({'success': True, 'users': users})

@app.route('/api/auth/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'ไม่พบผู้ใช้นี้ในฐานข้อมูล'}), 404

    if row['username'] in ['juner', 'cheer']:
        conn.close()
        return jsonify({'success': False, 'message': 'ไม่อนุญาตให้ลบบัญชีหลักของระบบ (จูนเนอร์/เชียร์)'}), 403

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'ลบผู้ใช้ {row["name"]} (@{row["username"]}) เรียบร้อยแล้ว'})

# ----------------- Products API -----------------
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row['id'],
            'title': row['title'],
            'type': row['type'],
            'category': row['category'],
            'price': row['price'],
            'unit': row['unit'],
            'imgUrl': row['img_url'],
            'ownerUsername': row['owner_username'],
            'ownerName': row['owner_name'],
            'ownerRole': row['owner_role'],
            'description': row['description'],
            'status': row['status']
        })
    conn.close()
    return jsonify({'success': True, 'products': products})

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json() or {}
    title = str(data.get('title', '')).strip()
    p_type = str(data.get('type', 'rent')).strip()
    price = float(data.get('price', 0))
    desc = str(data.get('description', '')).strip()
    owner_username = str(data.get('ownerUsername', 'cheer')).strip()
    owner_name = str(data.get('ownerName', 'ผู้ใช้งาน')).strip()
    owner_role = str(data.get('ownerRole', 'นักศึกษา')).strip()

    p_id = 'p' + str(os.urandom(4).hex())
    unit = 'บาท/วัน' if p_type == 'rent' else 'บาท (มัดจำ)' if p_type == 'borrow' else 'บาท (ขายขาด)'
    img_url = 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500'

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (id, title, type, category, price, unit, img_url, owner_username, owner_name, owner_role, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (p_id, title, p_type, 'รายการใหม่', price, unit, img_url, owner_username, owner_name, owner_role, desc))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'เพิ่มสินค้าเรียบร้อยแล้ว!'})

# ----------------- Messages API -----------------
@app.route('/api/messages', methods=['GET'])
def get_messages():
    product_id = request.args.get('product_id', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages WHERE product_id = ? ORDER BY id ASC
    ''', (product_id,))
    rows = cursor.fetchall()
    messages = []
    for r in rows:
        messages.append({
            'id': r['id'],
            'productId': r['product_id'],
            'senderId': r['sender_id'],
            'senderName': r['sender_name'],
            'senderAvatar': r['sender_avatar'] or DEFAULT_AVATAR,
            'text': r['text'],
            'type': r['type'],
            'time': r['time']
        })
    conn.close()
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/messages', methods=['POST'])
def send_message():
    data = request.get_json() or {}
    product_id = str(data.get('productId', ''))
    sender_id = str(data.get('senderId', ''))
    sender_name = str(data.get('senderName', ''))
    text = str(data.get('text', '')).strip()
    msg_type = str(data.get('type', 'text'))
    time_str = str(data.get('time', ''))

    if not product_id or not text:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (product_id, sender_id, sender_name, sender_avatar, text, type, time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, sender_id, sender_name, DEFAULT_AVATAR, text, msg_type, time_str))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': msg_id})

if __name__ == '__main__':
    print("UniShare Flask Backend with SQLite starting on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
