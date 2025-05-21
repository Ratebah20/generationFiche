from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from auth import (
    register_user, login_user, refresh_access_token, 
    get_user_by_id, update_user, change_password
)

# Créer un Blueprint pour les routes d'authentification
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Endpoint pour enregistrer un nouvel utilisateur"""
    data = request.get_json()
    
    # Vérifier que les champs requis sont présents
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({
            "success": False, 
            "message": "Données manquantes. Veuillez fournir username, email et password."
        }), 400
    
    # Enregistrer l'utilisateur
    result = register_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name')
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint pour authentifier un utilisateur et générer un token JWT"""
    data = request.get_json()
    
    # Vérifier que les champs requis sont présents
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            "success": False, 
            "message": "Données manquantes. Veuillez fournir username et password."
        }), 400
    
    # Authentifier l'utilisateur
    result = login_user(data['username'], data['password'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Endpoint pour rafraîchir le token d'accès"""
    result = refresh_access_token()
    return jsonify(result), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Endpoint pour récupérer les infos de l'utilisateur connecté"""
    current_user = get_jwt_identity()
    
    if isinstance(current_user, dict) and 'id' in current_user:
        user_id = current_user['id']
    else:
        # Fallback si l'identité n'est pas au format attendu
        user_id = current_user
    
    result = get_user_by_id(user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Endpoint pour mettre à jour les infos de l'utilisateur connecté"""
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if isinstance(current_user, dict) and 'id' in current_user:
        user_id = current_user['id']
    else:
        user_id = current_user
    
    result = update_user(user_id, data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def update_password():
    """Endpoint pour changer le mot de passe de l'utilisateur connecté"""
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Vérifier que les champs requis sont présents
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({
            "success": False, 
            "message": "Données manquantes. Veuillez fournir current_password et new_password."
        }), 400
    
    if isinstance(current_user, dict) and 'id' in current_user:
        user_id = current_user['id']
    else:
        user_id = current_user
    
    result = change_password(
        user_id, 
        data['current_password'], 
        data['new_password']
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400
