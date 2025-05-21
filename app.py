from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, decode_token
from ai_generation import generate_product_description
from dotenv import load_dotenv
import os
import pymysql
import re
import json
from auth import setup_jwt
from routes_auth import auth_bp

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration de l'application
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'une-cle-secrete-par-defaut')
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# Configuration de JWT
jwt = setup_jwt(app)

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Fonction helper pour obtenir une connexion à la base de données
def get_db_connection():
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

# Routes pour les pages HTML
@app.route('/')
def index():
    return render_template('index.html', title='Accueil')

@app.route('/apropos')
def about():
    return render_template('about.html', title='À propos')

@app.route('/login')
def login_page():
    return render_template('login.html', title='Connexion')

@app.route('/register')
def register_page():
    return render_template('register.html', title='Création de compte')

# Route pour le dashboard (protégée par JWT)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    token = None
    
    # 1. Vérifier si nous recevons le token du formulaire POST
    if request.method == 'POST' and 'token' in request.form:
        token = request.form['token']
        print(f"Token reçu du formulaire POST: {token[:10]}... (longueur {len(token)})")
        
        # Stocker le token dans la session pour les futures requêtes
        session['access_token'] = token
    
    # 2. Sinon vérifier dans le header Authorization
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            print(f"Token trouvé dans l'en-tête Authorization: {token[:10]}...")
    
    # 3. Sinon vérifier dans la session Flask
    if not token and 'access_token' in session:
        token = session['access_token']
        print(f"Token trouvé dans la session Flask: {token[:10]}...")
    
    try:
        # Si un token est disponible, essayer de le décoder
        if token:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            try:
                # Utiliser le décodeur de la bibliothèque
                decoded = jwt_decode_token(token)
                # L'identité se trouve dans la clé 'sub' du token
                current_user = decoded.get('sub', {})
                print(f"Décodage réussi, valeur de 'sub': {current_user}")
            except Exception as e:
                print(f"Erreur pendant le décodage: {e}")
                # Essayer avec un décodage manuel (fallback)
                import jwt
                jwt_secret = app.config['JWT_SECRET_KEY']
                decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'], options={"verify_signature": True})
                current_user = decoded.get('sub', {})
            
            print(f"Token décodé avec succès. Utilisateur: {current_user}")
            
            # S'assurer que current_user est un dictionnaire avec les champs requis
            if isinstance(current_user, dict):
                user_data = current_user
            else:
                # Essayer de récupérer les informations complètes de l'utilisateur depuis la BD
                from auth import get_user_by_id
                user_result = get_user_by_id(current_user)
                
                if user_result['success']:
                    user_data = user_result['user']
                else:
                    # Fallback au cas où les informations ne sont pas disponibles
                    user_data = {
                        'id': current_user if isinstance(current_user, int) else 0,
                        'username': current_user if isinstance(current_user, str) else 'Utilisateur',
                        'is_admin': False
                    }
            
            # Rendre explicitement le template dashboard
            return render_template('dashboard.html', title='Tableau de bord', user=user_data)
    except Exception as e:
        print(f"Erreur de décodage du token: {e}")
    
    # Si pas de token ou erreur de décodage, rediriger vers login
    print("Redirection vers la page de connexion - token absent ou invalide")
    return redirect(url_for('login_page', message="Veuillez vous connecter pour accéder au tableau de bord"))

# Route API protégée
@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Route API pour tester la connexion à la base de données
@app.route('/api/test-db', methods=['GET'])
def test_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "tables": [table["Tables_in_" + conn.db.decode('utf8')] for table in tables]}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Gestionnaire d'erreurs pour les endpoints API
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "Endpoint non trouvé"}), 404
    return render_template('404.html', title='Page non trouvée'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "Méthode non autorisée"}), 405
    return render_template('error.html', title='Erreur', message="Méthode non autorisée"), 405

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "Erreur serveur interne"}), 500
    return render_template('error.html', title='Erreur', message="Erreur serveur interne"), 500

# Fonction pour sauvegarder une fiche générée dans la base de données
def save_generated_fiche(user_id, product_name, prompt_used, generated_content, model_type='standard', include_images=True, include_price=True, include_comparison=False):
    try:
        # Obtenir une connexion à la base de données
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Préparer la requête SQL
        query = """
        INSERT INTO generated_fiches 
        (user_id, product_name, prompt_used, generated_content, model_type, include_images, include_price, include_comparison) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Exécuter la requête
        cursor.execute(query, (
            user_id, 
            product_name, 
            prompt_used, 
            generated_content, 
            model_type, 
            include_images, 
            include_price, 
            include_comparison
        ))
        
        # Récupérer l'ID de la fiche insérée
        fiche_id = cursor.lastrowid
        
        # Valider la transaction
        connection.commit()
        
        # Fermer le curseur et la connexion
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "fiche_id": fiche_id
        }
    
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la fiche générée: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la sauvegarde: {str(e)}"
        }

# Fonction pour récupérer l'historique des fiches générées par un utilisateur
def get_user_generated_fiches(user_id):
    try:
        # Obtenir une connexion à la base de données
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Préparer la requête SQL
        query = """
        SELECT id, product_name, model_type, include_images, include_price, include_comparison, created_at 
        FROM generated_fiches 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        """
        
        # Exécuter la requête
        cursor.execute(query, (user_id,))
        
        # Récupérer les résultats
        fiches = cursor.fetchall()
        
        # Fermer le curseur et la connexion
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "fiches": fiches
        }
    
    except Exception as e:
        print(f"Erreur lors de la récupération des fiches générées: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération: {str(e)}"
        }

# Fonction pour récupérer une fiche générée spécifique
def get_generated_fiche_by_id(fiche_id):
    try:
        # Obtenir une connexion à la base de données
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Préparer la requête SQL
        query = """
        SELECT * FROM generated_fiches WHERE id = %s
        """
        
        # Exécuter la requête
        cursor.execute(query, (fiche_id,))
        
        # Récupérer le résultat
        fiche = cursor.fetchone()
        
        # Fermer le curseur et la connexion
        cursor.close()
        connection.close()
        
        if fiche:
            return {
                "success": True,
                "fiche": fiche
            }
        else:
            return {
                "success": False,
                "message": "Fiche non trouvée"
            }
    
    except Exception as e:
        print(f"Erreur lors de la récupération de la fiche: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération: {str(e)}"
        }

# Routes pour la génération de fiches produit
@app.route('/generate-product', methods=['GET', 'POST'])
def generate_product_page():
    # Vérifier si l'utilisateur est authentifié - même mécanisme que le dashboard
    token = None
    
    # 1. Vérifier si nous recevons le token du formulaire POST
    if request.method == 'POST' and 'token' in request.form:
        token = request.form['token']
        print(f"Token reçu du formulaire POST: {token[:10]}... (longueur {len(token)})")
        
        # Stocker le token dans la session pour les futures requêtes
        session['access_token'] = token
    
    # 2. Sinon vérifier dans le header Authorization
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            print(f"Token trouvé dans l'en-tête Authorization: {token[:10]}...")
    
    # 3. Sinon vérifier dans la session Flask
    if not token and 'access_token' in session:
        token = session['access_token']
        print(f"Token trouvé dans la session Flask: {token[:10]}...")
    
    try:
        # Si un token est disponible, essayer de le décoder
        if token:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            try:
                # Utiliser le décodeur de la bibliothèque
                decoded = jwt_decode_token(token)
                # L'identité se trouve dans la clé 'sub' du token
                current_user = decoded.get('sub', {})
                print(f"Décodage réussi pour la page de génération, sub: {current_user}")
                
                # Préparer les données utilisateur pour le template
                if isinstance(current_user, dict):
                    user_data = current_user
                else:
                    from auth import get_user_by_id
                    user_result = get_user_by_id(current_user)
                    if user_result['success']:
                        user_data = user_result['user']
                    else:
                        # Fallback si get_user_by_id échoue
                        user_data = {
                            'id': current_user if isinstance(current_user, int) else 0,
                            'username': current_user if isinstance(current_user, str) else 'Utilisateur',
                            'is_admin': False
                        }
                
                # Rendre le template de génération de produit
                return render_template('generate_product.html', title='Génération de Produit', user=user_data)
            except Exception as e:
                print(f"Erreur pendant le décodage pour la page de génération: {e}")
    except Exception as e:
        print(f"Erreur globale pour la page de génération: {e}")
    
    # Si pas de token ou erreur de décodage, rediriger vers login
    print("Redirection vers la page de connexion - non authentifié pour la génération")
    return redirect(url_for('login_page', message="Veuillez vous connecter pour accéder à la génération de produit"))

@app.route('/api/generate-product', methods=['POST'])
def api_generate_product():
    # Vérifier l'authentification de plusieurs façons, comme pour les autres routes
    token = None
    authenticated = False
    
    # Vérifier dans le header Authorization
    auth_header = request.headers.get('Authorization', '')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print(f"API: Token trouvé dans l'en-tête Authorization: {token[:10]}...")
    
    # Sinon, vérifier dans la session Flask
    if not token and 'access_token' in session:
        token = session['access_token']
        print(f"API: Token trouvé dans la session Flask: {token[:10]}...")
    
    # Vérifier la validité du token
    if token:
        try:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            decoded = jwt_decode_token(token)
            authenticated = True
        except Exception as e:
            print(f"API: Erreur de décodage du token: {e}")
    
    if not authenticated:
        return jsonify({
            "success": False,
            "message": "Accès non autorisé. Veuillez vous connecter."
        }), 401
    
    # Récupérer les données du formulaire
    data = request.get_json()
    if not data or 'product_name' not in data:
        return jsonify({
            "success": False,
            "message": "Nom du produit manquant"
        }), 400
    
    # Récupérer les options de génération
    model_type = data.get('model_type', 'standard')
    include_images = data.get('include_images', True)
    include_price = data.get('include_price', True)
    include_comparison = data.get('include_comparison', False)
    
    # Générer la fiche produit avec les options
    result = generate_product_description(
        data['product_name'],
        model_type=model_type,
        include_images=include_images,
        include_price=include_price,
        include_comparison=include_comparison
    )
    
    if result['success']:
        # Récupérer l'ID de l'utilisateur à partir du token
        try:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            decoded = jwt_decode_token(token)
            user_id = decoded.get('sub')
            
            # Si l'ID utilisateur est un dictionnaire, extraire l'ID
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            
            # Construire le prompt utilisé pour la sauvegarde
            prompt_info = {
                'product_name': data['product_name'],
                'model_type': model_type,
                'include_images': include_images,
                'include_price': include_price,
                'include_comparison': include_comparison
            }
            
            # Sauvegarder la fiche générée dans la base de données
            save_result = save_generated_fiche(
                user_id=user_id,
                product_name=data['product_name'],
                prompt_used=json.dumps(prompt_info),
                generated_content=result['content'],
                model_type=model_type,
                include_images=include_images,
                include_price=include_price,
                include_comparison=include_comparison
            )
            
            # Ajouter l'information de sauvegarde au résultat
            if save_result['success']:
                result['fiche_id'] = save_result['fiche_id']
                result['saved'] = True
            else:
                result['saved'] = False
                result['save_error'] = save_result['message']
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la fiche: {e}")
            result['saved'] = False
            result['save_error'] = str(e)
        
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# Route pour afficher l'historique des fiches générées
@app.route('/history', methods=['GET'])
def history_page():
    token = None
    
    # Vérifier dans le header Authorization
    auth_header = request.headers.get('Authorization', '')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    # Sinon vérifier dans la session Flask
    if not token and 'access_token' in session:
        token = session['access_token']
    
    try:
        # Si un token est disponible, essayer de le décoder
        if token:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            try:
                # Utiliser le décodeur de la bibliothèque
                decoded = jwt_decode_token(token)
                # L'identité se trouve dans la clé 'sub' du token
                current_user = decoded.get('sub', {})
                
                # Préparer les données utilisateur pour le template
                if isinstance(current_user, dict):
                    user_data = current_user
                    user_id = user_data.get('id')
                else:
                    from auth import get_user_by_id
                    user_result = get_user_by_id(current_user)
                    if user_result['success']:
                        user_data = user_result['user']
                        user_id = current_user
                    else:
                        # Fallback si get_user_by_id échoue
                        user_data = {
                            'id': current_user if isinstance(current_user, int) else 0,
                            'username': current_user if isinstance(current_user, str) else 'Utilisateur',
                            'is_admin': False
                        }
                        user_id = user_data['id']
                
                # Récupérer l'historique des fiches générées par l'utilisateur
                history_result = get_user_generated_fiches(user_id)
                
                if history_result['success']:
                    # Rendre le template avec l'historique
                    return render_template(
                        'history.html', 
                        title='Historique des fiches générées', 
                        user=user_data,
                        fiches=history_result['fiches']
                    )
                else:
                    return render_template(
                        'history.html', 
                        title='Historique des fiches générées', 
                        user=user_data,
                        error=history_result['message'],
                        fiches=[]
                    )
                    
            except Exception as e:
                print(f"Erreur pendant le décodage pour la page d'historique: {e}")
    except Exception as e:
        print(f"Erreur globale pour la page d'historique: {e}")
    
    # Si pas de token ou erreur de décodage, rediriger vers login
    return redirect(url_for('login_page', message="Veuillez vous connecter pour accéder à l'historique"))

# Route pour afficher une fiche spécifique
@app.route('/fiche/<int:fiche_id>', methods=['GET'])
def view_fiche(fiche_id):
    token = None
    
    # Vérifier dans le header Authorization
    auth_header = request.headers.get('Authorization', '')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    # Sinon vérifier dans la session Flask
    if not token and 'access_token' in session:
        token = session['access_token']
    
    try:
        # Si un token est disponible, essayer de le décoder
        if token:
            from flask_jwt_extended.utils import decode_token as jwt_decode_token
            try:
                # Utiliser le décodeur de la bibliothèque
                decoded = jwt_decode_token(token)
                # L'identité se trouve dans la clé 'sub' du token
                current_user = decoded.get('sub', {})
                
                # Préparer les données utilisateur pour le template
                if isinstance(current_user, dict):
                    user_data = current_user
                    user_id = user_data.get('id')
                else:
                    from auth import get_user_by_id
                    user_result = get_user_by_id(current_user)
                    if user_result['success']:
                        user_data = user_result['user']
                        user_id = current_user
                    else:
                        # Fallback si get_user_by_id échoue
                        user_data = {
                            'id': current_user if isinstance(current_user, int) else 0,
                            'username': current_user if isinstance(current_user, str) else 'Utilisateur',
                            'is_admin': False
                        }
                        user_id = user_data['id']
                
                # Récupérer la fiche spécifique
                fiche_result = get_generated_fiche_by_id(fiche_id)
                
                if fiche_result['success']:
                    fiche = fiche_result['fiche']
                    
                    # Vérifier que l'utilisateur est autorisé à voir cette fiche
                    if fiche['user_id'] == user_id or user_data.get('is_admin', False):
                        # Rendre le template avec la fiche
                        return render_template(
                            'view_fiche.html', 
                            title=f'Fiche: {fiche["product_name"]}', 
                            user=user_data,
                            fiche=fiche
                        )
                    else:
                        return render_template(
                            'error.html',
                            title='Accès refusé',
                            message="Vous n'êtes pas autorisé à accéder à cette fiche."
                        ), 403
                else:
                    return render_template(
                        'error.html',
                        title='Fiche non trouvée',
                        message=fiche_result['message']
                    ), 404
                    
            except Exception as e:
                print(f"Erreur pendant le décodage pour la page de fiche: {e}")
    except Exception as e:
        print(f"Erreur globale pour la page de fiche: {e}")
    
    # Si pas de token ou erreur de décodage, rediriger vers login
    return redirect(url_for('login_page', message="Veuillez vous connecter pour accéder à cette fiche"))

# Lancer l'application Flask
if __name__ == '__main__':
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('PORT', 5000)))
