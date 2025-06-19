
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import hashlib
import base64
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'digital_signature_secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

# Tạo thư mục upload nếu chưa có
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Lưu trữ tạm thời keys và signatures
users_data = {}

def generate_key_pair():
    """Tạo cặp khóa RSA"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def hash_file(file_path):
    """Tạo hash từ file"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def sign_hash(private_key_pem, hash_value):
    """Ký hash bằng private key"""
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )
    
    signature = private_key.sign(
        hash_value.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    return base64.b64encode(signature).decode()

def verify_signature(public_key_pem, hash_value, signature):
    """Xác thực chữ ký"""
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        signature_bytes = base64.b64decode(signature)
        
        public_key.verify(
            signature_bytes,
            hash_value.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client')
def client():
    return render_template('client.html')

@app.route('/server')
def server():
    return render_template('server.html')

@socketio.on('connect')
def on_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_room')
def on_join_room(data):
    room = data['room']
    join_room(room)
    emit('status', {'message': f'Joined {room} room'})

@socketio.on('generate_keys')
def handle_generate_keys():
    """Tạo cặp khóa cho client"""
    try:
        private_key, public_key = generate_key_pair()
        
        users_data[request.sid] = {
            'private_key': private_key,
            'public_key': public_key
        }
        
        emit('keys_generated', {
            'private_key': private_key.decode(),
            'public_key': public_key.decode(),
            'status': 'success'
        })
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('upload_file')
def handle_file_upload(data):
    """Xử lý upload file và tạo hash"""
    try:
        file_data = data['file_data']
        filename = secure_filename(data['filename'])
        
        # Decode base64 file data
        file_content = base64.b64decode(file_data.split(',')[1])
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create hash
        file_hash = hash_file(file_path)
        
        # Store file info
        if request.sid not in users_data:
            users_data[request.sid] = {}
        
        users_data[request.sid]['file_path'] = file_path
        users_data[request.sid]['file_hash'] = file_hash
        users_data[request.sid]['filename'] = filename
        
        emit('file_uploaded', {
            'filename': filename,
            'hash': file_hash,
            'status': 'success'
        })
        
        # Gửi thông tin đến server room
        socketio.emit('file_info', {
            'filename': filename,
            'hash': file_hash,
            'from_client': request.sid
        }, room='server')
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('sign_data')
def handle_sign_data():
    """Ký dữ liệu"""
    try:
        user_data = users_data.get(request.sid)
        if not user_data or 'private_key' not in user_data or 'file_hash' not in user_data:
            emit('error', {'message': 'Missing data for signing'})
            return
        
        # Sign the hash
        signature = sign_hash(user_data['private_key'], user_data['file_hash'])
        
        user_data['signature'] = signature
        
        emit('data_signed', {
            'signature': signature,
            'status': 'success'
        })
        
        # Gửi chữ ký đến server
        socketio.emit('signature_received', {
            'signature': signature,
            'public_key': user_data['public_key'].decode(),
            'hash': user_data['file_hash'],
            'filename': user_data['filename'],
            'from_client': request.sid
        }, room='server')
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('verify_signature')
def handle_verify_signature(data):
    """Xác thực chữ ký"""
    try:
        public_key_pem = data['public_key'].encode()
        hash_value = data['hash']
        signature = data['signature']
        
        is_valid = verify_signature(public_key_pem, hash_value, signature)
        
        emit('verification_result', {
            'is_valid': is_valid,
            'filename': data.get('filename', ''),
            'status': 'success'
        })
        
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
