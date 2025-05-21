import os
import sys
from dotenv import load_dotenv

def test_openai_key():
    """Test la validité de la clé API OpenAI configurée dans le fichier .env"""
    # Charger les variables d'environnement depuis le fichier .env
    load_dotenv()
    
    # Récupérer la clé API OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("Erreur: La variable OPENAI_API_KEY n'est pas définie dans le fichier .env")
        print("Veuillez ajouter votre clé API OpenAI dans le fichier .env :")
        print("OPENAI_API_KEY=votre_cle_api_openai")
        return False
    
    print(f"Tentative de connexion à l'API OpenAI avec la clé configurée...")
    # Afficher seulement le début et la fin de la clé pour des raisons de sécurité
    if len(api_key) > 10:
        masked_key = f"{api_key[:6]}{'*' * 10}{api_key[-4:]}"
    else:
        masked_key = "*****" # Fallback pour les clés très courtes
    print(f"Clé utilisée: {masked_key}")
    
    # Utiliser requests plutôt que le client Python pour éviter les problèmes de dépendances
    try:
        import requests
        
        # URL de l'API pour vérifier les modèles disponibles
        url = "https://api.openai.com/v1/models"
        
        # En-têtes avec l'authentification
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Faire la requête
        response = requests.get(url, headers=headers)
        
        # Vérifier le code de statut
        if response.status_code == 200:
            # La clé est valide et la requête a réussi
            data = response.json()
            models = data.get("data", [])
            
            print("\n✅ Succès! Votre clé API OpenAI est valide.")
            
            if models:
                print(f"\nModèles disponibles avec votre clé API (montrant les 5 premiers):")
                # Afficher jusqu'à 5 modèles
                for i, model in enumerate(models[:5]):
                    print(f"- {model.get('id')}")
                
                if len(models) > 5:
                    print(f"... et {len(models) - 5} autres modèles")
            else:
                print("\nAucun modèle n'a été trouvé pour votre clé API.")
                
            return True
            
        elif response.status_code == 401:
            # Problème d'authentification
            print("\n❌ Erreur d'authentification: Votre clé API est invalide ou a expiré.")
            print(f"Détails: {response.json().get('error', {}).get('message', 'Aucun détail disponible')}")
            
        elif response.status_code == 429:
            # Rate limit atteint
            print("\n❌ Limite de taux atteinte: Vous avez effectué trop de requêtes avec cette clé API.")
            print(f"Détails: {response.json().get('error', {}).get('message', 'Aucun détail disponible')}")
            
        else:
            # Autre erreur
            print(f"\n❌ Erreur (Code {response.status_code}):")
            print(f"Détails: {response.json().get('error', {}).get('message', 'Aucun détail disponible')}")
            
    except ImportError:
        print("\n❌ Erreur: Le module 'requests' n'est pas installé.")
        print("Exécutez 'pip install requests' pour l'installer.")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("La connexion à l'API OpenAI a échoué.")
        print("Vérifiez que votre clé est correcte et que vous avez accès à l'API OpenAI.")
    
    return False

def main():
    print("\n=== Test de la clé API OpenAI ===\n")
    if test_openai_key():
        print("\nVotre clé API OpenAI est correctement configurée et fonctionne.")
    else:
        print("\nLa vérification de votre clé API OpenAI a échoué.")
        print("Veuillez vérifier votre clé et réessayer.")

if __name__ == "__main__":
    main()
