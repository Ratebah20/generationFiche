# Projet de Génération de Fiches Produit Avec l'IA Générative

## J'ai choisi des fiches de produit automobile

### Mise en place initiale

J'ai commencé par créer une application Flask minimaliste pour servir de base à mon projet. Cette étape a été relativement simple, avec la mise en place des fichiers essentiels :
- `app.py` : le fichier principal contenant la logique de l'application
- `requirements.txt` : pour lister les dépendances
- `.env` : pour stocker les variables d'environnement sensibles
- Un dossier `templates` pour les vues HTML

J'ai opté pour une structure simple mais évolutive, permettant d'ajouter facilement des fonctionnalités au fur et à mesure du développement. Cette approche m'a permis de tester rapidement les concepts de base avant de me lancer dans des fonctionnalités plus complexes.

### Système d'authentification JWT

L'implémentation du système d'authentification JWT a été l'une des parties les plus complexes du projet. J'ai choisi JWT car il offre une solution stateless, idéale pour les API et les applications modernes.

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


La difficulté principale a été de gérer correctement le cycle de vie des tokens JWT. J'ai dû :
1. Implémenter un système de tokens d'accès et de rafraîchissement
2. Configurer la durée de validité des tokens
3. Créer des routes API RESTful pour l'authentification
4. Développer un middleware pour protéger les routes sensibles

Un défi particulier a été la gestion des tokens côté client. J'ai utilisé `localStorage` pour stocker les tokens, mais cela a posé des problèmes de sécurité que j'ai dû résoudre. J'ai également dû gérer les cas où le token est présent dans différents contextes (en-tête Authorization, session Flask, formulaire POST).

### Intégration de l'API OpenAI

L'intégration de l'API OpenAI pour générer les fiches produit a été une étape fascinante. J'ai créé un module `ai_generation.py` qui encapsule toute la logique d'interaction avec l'API.

Le plus grand défi a été de construire des prompts efficaces qui produisent des fiches produit bien structurées. J'ai dû expérimenter avec différentes formulations et instructions pour obtenir des résultats cohérents et professionnels.

J'ai également dû gérer les cas d'erreur, comme les problèmes de connexion à l'API ou les limites de rate-limiting. La gestion des clés API de manière sécurisée via les variables d'environnement était également cruciale.

### Interface utilisateur et expérience utilisateur

Pour l'interface utilisateur, j'ai opté pour Bootstrap comme framework CSS de base, que j'ai personnalisé pour obtenir un design moderne et professionnel. J'ai utilisé des polices Google Fonts pour améliorer la typographie et Font Awesome pour les icônes.

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
