import os
import re
import pymysql
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256

# Charger les variables d'environnement
load_dotenv()

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
    
    # Se connecter sans spécifier la base de données pour pouvoir la créer si elle n'existe pas
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        port=int(port),
        charset=params.get('charset', 'utf8mb4')
    )
    
    return connection, database

def initialize_database():
    """
    Initialise la base de données et crée la table users
    """
    try:
        # Obtenir une connexion à MySQL (sans spécifier de base de données)
        connection, db_name = get_db_connection()
        cursor = connection.cursor()
        
        print(f"Connexion à MySQL réussie.")
        
        # Créer la base de données si elle n'existe pas
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Base de données '{db_name}' créée ou vérifiée avec succès.")
        
        # Utiliser la base de données
        cursor.execute(f"USE `{db_name}`")
        
        # Créer la table des utilisateurs
        users_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50) NOT NULL UNIQUE,
          email VARCHAR(100) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          first_name VARCHAR(50),
          last_name VARCHAR(50),
          is_active BOOLEAN DEFAULT TRUE,
          is_admin BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          last_login TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        '''
        cursor.execute(users_table_sql)
        print("Table 'users' créée ou vérifiée avec succès.")
        
        # Vérifier si un utilisateur admin existe déjà
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Créer un utilisateur administrateur par défaut
            admin_password = "admin123"
            hashed_password = pbkdf2_sha256.hash(admin_password)
            
            insert_admin_sql = '''
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            
            cursor.execute(insert_admin_sql, (
                'admin',
                'admin@example.com',
                hashed_password,
                'Admin',
                'User',
                True,
                True
            ))
            
            print("Utilisateur administrateur créé avec succès:")
            print("  - Nom d'utilisateur: admin")
            print("  - Mot de passe: admin123")
            print("  - Email: admin@example.com")
            print("ATTENTION: Veuillez changer ce mot de passe après la première connexion.")
        else:
            print("Un utilisateur 'admin' existe déjà.")
        
        # Vérifier et créer les index pour optimiser les requêtes
        try:
            # Vérifier si l'index username existe
            cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_username'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_username ON users(username)")
                print("Index sur username créé.")
            else:
                print("Index sur username existe déjà.")
                
            # Vérifier si l'index email existe
            cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_email'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_email ON users(email)")
                print("Index sur email créé.")
            else:
                print("Index sur email existe déjà.")
        except Exception as e:
            print(f"Avertissement lors de la création des index: {e}")
            print("L'application fonctionnera même sans ces index.")
            # Continuer sans les index - ce n'est pas critique
        
        connection.commit()
        print("Initialisation de la base de données terminée avec succès.")
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    finally:
        connection.close()
        print("Connexion à MySQL fermée.")

if __name__ == "__main__":
    print("Initialisation de la base de données...")
    initialize_database()
