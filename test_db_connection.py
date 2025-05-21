import os
import re
import pymysql
from dotenv import load_dotenv

def main():
    # Charger les variables d'environnement depuis le fichier .env
    load_dotenv()
    
    # Récupérer l'URL de la base de données
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("Erreur: La variable DATABASE_URL n'est pas définie dans le fichier .env")
        return
    
    print(f"Tentative de connexion à: {db_url}")
    
    # Analyser l'URL de la base de données
    pattern = r"mysql://([^:]+):([^@]*)@([^:]+):(\d+)/([^?]+)"
    match = re.match(pattern, db_url)
    
    if not match:
        print("Erreur: Format de DATABASE_URL incorrect.")
        print("Format attendu: mysql://user:password@host:port/database")
        return
    
    user, password, host, port, database = match.groups()
    
    # Extraire les paramètres additionnels (comme charset)
    params = {}
    if '?' in db_url:
        query_string = db_url.split('?')[1]
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=')
                params[key] = value
    
    try:
        # Tenter de se connecter à la base de données
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=int(port),
            charset=params.get('charset', 'utf8mb4')
        )
        
        print("Connexion réussie à la base de données !")
        
        # Vérifier si la base de données existe
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print(f"\nTables existantes dans la base de données '{database}':")
                for table in tables:
                    print(f"- {table[0]}")
            else:
                print(f"\nLa base de données '{database}' existe mais ne contient aucune table.")
        
        connection.close()
        print("\nConnexion fermée.")
        
    except Exception as e:
        print(f"Erreur lors de la connexion à la base de données: {e}")
        
        # Vérifier si la base de données existe
        if "Unknown database" in str(e):
            try:
                # Se connecter sans spécifier la base de données
                conn = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    port=int(port),
                    charset=params.get('charset', 'utf8mb4')
                )
                
                print("\nConnexion au serveur MySQL réussie, mais la base de données spécifiée n'existe pas.")
                print(f"Voulez-vous créer la base de données '{database}' ? (o/n)")
                response = input().lower()
                
                if response == 'o':
                    with conn.cursor() as cursor:
                        cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"Base de données '{database}' créée avec succès!")
                
                conn.close()
                
            except Exception as e2:
                print(f"Erreur lors de la connexion au serveur MySQL: {e2}")

if __name__ == "__main__":
    main()
