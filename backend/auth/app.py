from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import hashlib
import os
from User import User

app = Flask(__name__)
CORS(app)

# Configuración MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'cuenta_confiable')

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
users_collection = db['users']

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Verificar si el usuario ya existe
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'error': 'El correo ya está registrado'}), 400
        
        # Crear nuevo usuario
        user = User(
            name=data['name'],
            email=data['email'],
            user_type=data['userType'],
            password=hash_password(data['password'])
        )
        
        result = users_collection.insert_one(user.to_dict())
        user_id = str(result.inserted_id)
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user_id,
                'name': user.name,
                'email': user.email,
                'user_type': user.user_type
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data['email']
        password = hash_password(data['password'])
        
        user = users_collection.find_one({'email': email, 'password': password})
        
        if not user:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        return jsonify({
            'message': 'Login exitoso',
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'user_type': user['user_type']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
def verify_user():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'valid': False, 'error': 'user_id requerido'}), 400
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'valid': False}), 404
        
        return jsonify({
            'valid': True,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'user_type': user['user_type']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)