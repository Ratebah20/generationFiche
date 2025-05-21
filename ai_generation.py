import os
import requests
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def generate_product_description(product_name, model_type='standard', include_images=True, include_price=True, include_comparison=False):
    """
    Génère une fiche produit complète pour un produit automobile
    
    Args:
        product_name (str): Nom du produit automobile
        model_type (str): Type de modèle de génération ('standard' ou 'detailed')
        include_images (bool): Inclure des suggestions d'images
        include_price (bool): Inclure une estimation de prix
        include_comparison (bool): Inclure une comparaison avec les concurrents
    
    Returns:
        dict: Résultat de la génération avec succès/échec et données
    """
    # Récupérer la clé API depuis les variables d'environnement
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return {
            "success": False,
            "message": "Clé API OpenAI non configurée. Veuillez configurer la variable d'environnement OPENAI_API_KEY."
        }
    
    # Construction du prompt avec le nom de produit et les options
    sections = [
        "1. Une description générale du véhicule",
        "2. Les caractéristiques techniques (moteur, puissance, consommation, etc.)",
        "3. Les équipements de série",
        "4. Les options disponibles",
        "5. Les points forts du véhicule"
    ]
    
    # Ajouter des sections en fonction des options sélectionnées
    if include_price:
        sections.append("6. Une section prix et disponibilité")
    
    if include_images:
        sections.append("7. Des suggestions d'images et de visuels marketing (descriptions textuelles)")
    
    if include_comparison:
        sections.append("8. Une comparaison avec les principaux concurrents du segment")
    
    # Déterminer le niveau de détail en fonction du modèle
    detail_level = "très détaillée et approfondie" if model_type == "detailed" else "bien structurée et concise"
    
    # Construction du prompt final
    prompt = f"""Crée une fiche produit {detail_level} pour un véhicule automobile nommé {product_name}.
    
    La fiche doit inclure :
    {chr(10).join(sections)}
    
    Format ta réponse en HTML structuré avec des sections clairement définies, des titres (h1, h2, h3),
    des paragraphes et des listes à puces pour faciliter la lecture.
    
    {'Sois exhaustif et technique dans la description et les caractéristiques.' if model_type == 'detailed' else 'Reste concis tout en étant informatif.'}
    """
    
    # Configuration de la requête API OpenAI
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Construction du corps de la requête
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un expert en marketing automobile qui crée des fiches produit détaillées et professionnelles."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1200
    }
    
    try:
        # Envoi de la requête à l'API
        response = requests.post(api_url, headers=headers, json=payload)
        response_data = response.json()
        
        # Vérification de la réponse
        if response.status_code == 200 and "choices" in response_data:
            # Extraction du contenu généré
            generated_content = response_data["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "product_name": product_name,
                "content": generated_content
            }
        else:
            # Gestion des erreurs de l'API
            error_message = response_data.get("error", {}).get("message", "Erreur inconnue")
            return {
                "success": False,
                "message": f"Erreur lors de la génération: {error_message}"
            }
    
    except Exception as e:
        # Gestion des exceptions
        return {
            "success": False,
            "message": f"Erreur lors de la communication avec l'API: {str(e)}"
        }
