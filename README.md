# Projet de Génération de Fiches Produit Avec l'IA Générative

## J'ai choisi des fiches de produit automobile

### Mise en place initiale

J'ai commencé par créer une application Flask minimaliste pour servir de base à mon projet. Cette étape a été relativement simple, avec la mise en place des fichiers essentiels :
- `app.py` : le fichier principal contenant la logique de l'application
- `requirements.txt` : pour lister les dépendances
- `.env` : pour stocker les variables d'environnement sensibles
- Un dossier `templates` pour les vues HTML

J'ai opté pour une structure simple mais évolutive, permettant d'ajouter facilement des fonctionnalités au fur et à mesure du développement. Cette approche m'a permis de tester rapidement les concepts de base avant de me lancer dans des fonctionnalités plus complexes.

J'ai d'abord créé la table `users` dans MySQL avec les champs nécessaires :
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
![image](https://github.com/user-attachments/assets/f85277bf-7c5d-4b8b-ae18-0f275e60033b)

### Système d'authentification JWT

L'implémentation du système d'authentification JWT a été l'une des parties les plus complexes du projet. J'ai choisi JWT car il offre une solution stateless, idéale pour les API et les applications modernes.


La difficulté principale a été de gérer correctement le cycle de vie des tokens JWT. J'ai dû relever plusieurs défis techniques :

1. **Implémentation d'un système de tokens à deux niveaux** :
   - Token d'accès à courte durée (15 minutes) pour les opérations courantes
   - Token de rafraîchissement à longue durée (7 jours) pour obtenir un nouveau token d'accès sans reconnexion
   - Stockage sécurisé des tokens côté client (localStorage) avec vérification de l'expiration

2. **Configuration fine de la durée de validité des tokens** :
   - Équilibrage entre sécurité (durée courte) et expérience utilisateur (moins de reconnexions)
   - Gestion des fuseaux horaires et de la synchronisation des horloges entre client et serveur
   - Implémentation d'une logique de "sliding expiration" pour prolonger la session des utilisateurs actifs

3. **Création de routes API RESTful pour l'authentification** :
   - `/api/auth/register` : Création de compte avec validation des données et hachage sécurisé des mots de passe
   - `/api/auth/login` : Authentification et émission des tokens JWT
   - `/api/auth/refresh` : Renouvellement du token d'accès via le token de rafraîchissement
   - `/api/auth/logout` : Invalidation des tokens (côté client uniquement, les JWT étant stateless)

4. **Développement d'un middleware pour protéger les routes sensibles** :
   - Vérification de la présence et de la validité du token JWT dans chaque requête
   - Extraction des informations utilisateur du token pour les rendre disponibles dans le contexte de la requête
   - Gestion des erreurs d'authentification avec des messages appropriés
   - Mise en place de différents niveaux d'autorisation (utilisateur standard, administrateur)

Un défi particulier a été la gestion des tokens côté client. J'ai utilisé `localStorage` pour stocker les tokens, mais cela a posé des problèmes de sécurité que j'ai dû résoudre (notamment la vulnérabilité aux attaques XSS). J'ai également dû gérer les cas où le token est présent dans différents contextes (en-tête Authorization, session Flask, formulaire POST).

#### Cas d'utilisation : Processus complet d'authentification et d'accès sécurisé

Voici un exemple concret du flux d'authentification que j'ai implémenté :

1. **Inscription d'un nouvel utilisateur** :
   - L'utilisateur remplit le formulaire d'inscription avec son nom d'utilisateur, email et mot de passe
   - Le système valide les données (format d'email, force du mot de passe)
   - Le mot de passe est haché avec bcrypt avant stockage en base de données
   - Un compte est créé et l'utilisateur est redirigé vers la page de connexion

2. **Connexion et émission des tokens** :
   - L'utilisateur saisit ses identifiants sur la page de connexion
   - Le système vérifie les identifiants contre la base de données
   - En cas de succès, deux tokens JWT sont générés :
     * Token d'accès (courte durée) contenant l'ID utilisateur et ses rôles
     * Token de rafraîchissement (longue durée) pour renouveler le token d'accès
   - Les tokens sont retournés à l'application cliente qui les stocke dans localStorage

3. **Accès aux ressources protégées** :
   - Pour chaque requête à une API protégée, le client inclut le token d'accès dans l'en-tête HTTP
   - Le middleware d'authentification intercepte la requête et vérifie la validité du token
   - Si le token est valide, la requête est traitée et les données sont retournées
   - Si le token est expiré, une erreur 401 est retournée

4. **Rafraîchissement du token** :
   - Lorsque le client reçoit une erreur 401 (token expiré), il utilise le token de rafraîchissement
   - Une requête est envoyée à `/api/auth/refresh` avec le token de rafraîchissement
   - Si ce token est valide, un nouveau token d'accès est émis
   - Le client remplace l'ancien token d'accès et réessaie sa requête originale

5. **Déconnexion** :
   - L'utilisateur clique sur "Déconnexion"
   - Les tokens sont supprimés du localStorage
   - L'utilisateur est redirigé vers la page d'accueil


### Intégration de l'API OpenAI

L'intégration de l'API OpenAI pour générer les fiches produit.
J'ai créé un module `ai_generation.py` qui encapsule toute la logique d'interaction avec l'API, de la construction des prompts à la gestion des réponses.

#### Architecture du système de génération

J'ai conçu une architecture modulaire pour la génération de fiches produit :

1. **Fonction principale** `generate_product_description()` qui accepte :
   - Le nom du produit (obligatoire)
   - Le type de modèle (standard ou détaillé)
   - Des options de personnalisation (inclusion d'images, de prix, de comparaisons)

2. **Système de construction de prompts dynamiques** qui adapte le contenu demandé en fonction des options sélectionnées par l'utilisateur.

#### Ingénierie de prompts avancée

Le plus grand défi a été de construire des prompts efficaces qui produisent des fiches produit bien structurées. Voici ma méthodologie :

1. **Structure en sections** : J'ai défini une liste de sections obligatoires et optionnelles :
   ```python
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
       sections.append("7. Des suggestions d'images et de visuels marketing")
   
   if include_comparison:
       sections.append("8. Une comparaison avec les principaux concurrents du segment")
   ```

2. **Instructions de formatage** : J'ai inclus des directives précises pour obtenir un format HTML structuré :
   ```python
   prompt += """Format ta réponse en HTML structuré avec des sections clairement définies, 
   des titres (h1, h2, h3), des paragraphes et des listes à puces pour faciliter la lecture."""
   ```

3. **Adaptation du niveau de détail** : J'ai varié le niveau de détail en fonction du modèle choisi :
   ```python
   detail_level = "très détaillée et approfondie" if model_type == "detailed" else "bien structurée et concise"
   
   prompt += f"""{'Sois exhaustif et technique dans la description et les caractéristiques.' 
              if model_type == 'detailed' else 'Reste concis tout en étant informatif.'}"""
   ```

4. **Rôle du système** : J'ai défini un rôle d'expert pour le modèle :
   ```python
   system_message = {"role": "system", "content": "Tu es un expert en marketing automobile qui crée des fiches produit détaillées et professionnelles."}
   ```

Cette approche m'a permis d'obtenir des résultats cohérents et de haute qualité, adaptés aux besoins spécifiques de chaque demande.

#### Optimisation des paramètres de génération

J'ai expérimenté avec différents paramètres pour trouver l'équilibre optimal entre créativité et cohérence :

```python
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        system_message,
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7,  # Équilibre entre créativité et cohérence
    "max_tokens": 1200  # Longueur suffisante pour des fiches détaillées
}
```


### Interface utilisateur et expérience utilisateur

Pour l'interface utilisateur, j'ai opté pour Bootstrap comme framework CSS de base, que j'ai personnalisé pour obtenir un design moderne. J'ai utilisé des polices Google Fonts pour améliorer la typographie et Font pour les icônes.

J'ai particulièrement travaillé sur la page de génération de produit (`generate_product.html`), en créant une interface en deux colonnes qui permet à l'utilisateur de :
- Saisir le nom du produit
- Choisir entre un modèle standard ou détaillé
- Sélectionner des options comme l'inclusion d'images, de prix ou de comparaisons
- Visualiser immédiatement le résultat généré

L'implémentation des fonctionnalités JavaScript pour copier, imprimer et télécharger les fiches a été un défi intéressant. J'ai dû travailler avec l'API Clipboard et créer des fenêtres d'impression personnalisées.

### Historisation des fiches générées

La dernière grande fonctionnalité que j'ai implémentée est l'historisation des fiches générées. J'ai créé une table `generated_fiches` pour stocker :
- Les informations de base (nom du produit, utilisateur)
- Le prompt utilisé
- Le contenu généré
- Les options sélectionnées
- La date de création

```sql
CREATE TABLE generated_fiches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    prompt_used TEXT NOT NULL,
    generated_content TEXT NOT NULL,
    model_type VARCHAR(50) DEFAULT 'standard',
    include_images BOOLEAN DEFAULT TRUE,
    include_price BOOLEAN DEFAULT TRUE,
    include_comparison BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

J'ai ensuite créé des fonctions pour sauvegarder et récupérer les fiches, ainsi que des pages pour afficher l'historique et consulter les fiches individuelles. Cette fonctionnalité a ajouté beaucoup de valeur à l'application, permettant aux utilisateurs de retrouver facilement leurs créations précédentes.

### Défis techniques et solutions

#### Gestion des sessions et de l'authentification

La gestion de l'authentification à travers différentes pages a été complexe. J'ai dû mettre en place un système qui vérifie la présence du token JWT à plusieurs endroits (en-tête HTTP, session Flask, formulaire) pour assurer une expérience utilisateur fluide.

J'ai également dû gérer les cas où le décodage du token échoue, en implémentant des fallbacks et des redirections vers la page de connexion.

#### Interaction avec la base de données

L'interaction directe avec MySQL via PyMySQL a posé quelques défis, notamment pour la gestion des transactions et la sécurisation des requêtes contre les injections SQL. J'ai utilisé des requêtes paramétrées pour éviter ces problèmes.

La structure de la fonction `get_db_connection()` a été conçue pour extraire les paramètres de connexion depuis la variable d'environnement `DATABASE_URL`, ce qui facilite le déploiement dans différents environnements.

#### Gestion des erreurs

J'ai mis en place un système complet de gestion des erreurs, avec des handlers pour les erreurs 404, 405 et 500. Cela permet d'afficher des messages d'erreur appropriés aux utilisateurs et de logger les problèmes pour le débogage.

### Conclusion

Ce projet m'a permis de mettre en pratique de nombreuses compétences en développement web :
- Développement backend avec Flask
- Authentification sécurisée avec JWT
- Intégration d'API tierces (OpenAI)
- Conception d'interfaces utilisateur modernes
- Gestion de base de données relationnelle

Les défis rencontrés m'ont poussé à approfondir ma compréhension de ces technologies et à trouver des solutions créatives. Le résultat est une application fonctionnelle et professionnelle qui répond parfaitement au besoin initial : générer des fiches produit de qualité pour des véhicules automobiles.
