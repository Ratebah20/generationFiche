import os
import re
import pymysql
from passlib.hash import pbkdf2_sha256
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime, timedelta
from email_validator import validate_email, EmailNotValidError

def get_db_connection():
    """
    Établit une connexion à la base de données à partir des variables d'environnement
    """
    db_url = os.getenv('DATABASE_URL')
    pattern = r"mysql://([^:]+):([^@]*)@([^:]+):(\d+)/([^?]+)"
    match = re.match(pattern, db_url)
    
    if not match:
        raise ValueError("Format de DATABASE_URL incorrect")
    
    user, password, host, port, database = match.groups()
    
    # Extraire les paramètres additionnels (comme charset)
    params = {}
    if '?' in db_url:
        query_string = db_url.split('?')[1]
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=')
                params[key] = value
    
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port),
        charset=params.get('charset', 'utf8mb4'),
        cursorclass=pymysql.cursors.DictCursor
    )

def setup_jwt(app):
    """
    Configure l'application Flask pour utiliser JWT
    """
    # Configuration JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'your-secret-key'))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    jwt = JWTManager(app)
    
    return jwt

def register_user(username, email, password, first_name=None, last_name=None):
    """
    Enregistre un nouvel utilisateur dans la base de données
    """
    # Valider l'email
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return {"success": False, "message": str(e)}
    
    # Vérifier que le mot de passe est suffisamment complexe
    if len(password) < 8:
        return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
    
    # Hasher le mot de passe
    password_hash = pbkdf2_sha256.hash(password)
    
    # Insérer l'utilisateur dans la base de données
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Vérifier si l'utilisateur existe déjà
            sql_check = "SELECT id FROM users WHERE username = %s OR email = %s"
            cursor.execute(sql_check, (username, email))
            if cursor.fetchone():
                return {"success": False, "message": "Nom d'utilisateur ou email déjà utilisé"}
            
            # Insérer le nouvel utilisateur
            sql = """
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (username, email, password_hash, first_name, last_name))
        
        conn.commit()
        return {"success": True, "message": "Utilisateur créé avec succès"}
    
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de l'enregistrement: {str(e)}"}
    
    finally:
        conn.close()

def login_user(username_or_email, password):
    """
    Authentifie un utilisateur et génère un token JWT
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Chercher l'utilisateur par nom d'utilisateur ou email
            sql = "SELECT id, username, email, password_hash, is_active, is_admin FROM users WHERE username = %s OR email = %s"
            cursor.execute(sql, (username_or_email, username_or_email))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "Identifiants invalides"}
            
            if not user['is_active']:
                return {"success": False, "message": "Compte désactivé"}
            
            # Vérifier le mot de passe
            if not pbkdf2_sha256.verify(password, user['password_hash']):
                return {"success": False, "message": "Identifiants invalides"}
            
            # Mettre à jour la date de dernière connexion
            sql_update = "UPDATE users SET last_login = NOW() WHERE id = %s"
            cursor.execute(sql_update, (user['id'],))
            conn.commit()
            
            # Créer les tokens JWT
            identity = {
                'id': user['id'],
                'username': user['username'],
                'is_admin': user['is_admin']
            }
            
            access_token = create_access_token(identity=identity)
            refresh_token = create_refresh_token(identity=identity)
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "is_admin": user['is_admin']
                }
            }
    
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de la connexion: {str(e)}"}
    
    finally:
        conn.close()

def refresh_access_token():
    """
    Régénère un token d'accès à partir du token de rafraîchissement
    """
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return {"success": True, "access_token": new_access_token}

def get_user_by_id(user_id):
    """
    Récupère les informations d'un utilisateur par son ID
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
            SELECT id, username, email, first_name, last_name, is_active, is_admin, 
                   created_at, updated_at, last_login 
            FROM users 
            WHERE id = %s
            """
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
            return {"success": True, "user": user}
    
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de la récupération: {str(e)}"}
    
    finally:
        conn.close()

def update_user(user_id, data):
    """
    Met à jour les informations d'un utilisateur
    """
    allowed_fields = {'email', 'first_name', 'last_name', 'is_active'}
    update_fields = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_fields:
        return {"success": False, "message": "Aucun champ valide à mettre à jour"}
    
    # Valider l'email si présent
    if 'email' in update_fields:
        try:
            valid = validate_email(update_fields['email'])
            update_fields['email'] = valid.email
        except EmailNotValidError as e:
            return {"success": False, "message": str(e)}
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Construire la requête SQL de mise à jour
            fields = ', '.join([f"{field} = %s" for field in update_fields.keys()])
            values = list(update_fields.values())
            values.append(user_id)
            
            sql = f"UPDATE users SET {fields} WHERE id = %s"
            cursor.execute(sql, values)
            
            if cursor.rowcount == 0:
                return {"success": False, "message": "Utilisateur non trouvé ou aucune modification"}
            
            conn.commit()
            return {"success": True, "message": "Utilisateur mis à jour avec succès"}
    
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de la mise à jour: {str(e)}"}
    
    finally:
        conn.close()

def change_password(user_id, current_password, new_password):
    """
    Change le mot de passe d'un utilisateur
    """
    if len(new_password) < 8:
        return {"success": False, "message": "Le nouveau mot de passe doit contenir au moins 8 caractères"}
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Récupérer l'utilisateur
            sql = "SELECT password_hash FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
            # Vérifier le mot de passe actuel
            if not pbkdf2_sha256.verify(current_password, user['password_hash']):
                return {"success": False, "message": "Mot de passe actuel incorrect"}
            
            # Hasher et enregistrer le nouveau mot de passe
            new_password_hash = pbkdf2_sha256.hash(new_password)
            sql_update = "UPDATE users SET password_hash = %s WHERE id = %s"
            cursor.execute(sql_update, (new_password_hash, user_id))
            
            conn.commit()
            return {"success": True, "message": "Mot de passe modifié avec succès"}
    
    except Exception as e:
        return {"success": False, "message": f"Erreur lors du changement de mot de passe: {str(e)}"}
    
    finally:
        conn.close()
