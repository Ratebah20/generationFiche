-- Script SQL pour créer la table utilisateur avec les champs nécessaires à l'authentification JWT

-- Vérifie si la base de données existe, sinon la crée
CREATE DATABASE IF NOT EXISTS generationFiche CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Utilise la base de données
USE generationFiche;

-- Supprime la table si elle existe déjà pour éviter les erreurs
DROP TABLE IF EXISTS users;

-- Crée la table utilisateur
CREATE TABLE users (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ajoute un utilisateur administrateur par défaut (mot de passe à hasher dans l'application)
-- Le mot de passe sera 'admin123' (sera hashé lors de l'insertion réelle)
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_admin)
VALUES 
('admin', 'admin@example.com', 'placeholder_for_hashed_password', 'Admin', 'User', TRUE, TRUE);

-- Ajout d'index pour optimiser les requêtes
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_email ON users(email);
