-- Script pour créer la table des fiches produit générées
CREATE TABLE IF NOT EXISTS generated_fiches (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Index pour accélérer les recherches par utilisateur
CREATE INDEX idx_user_id ON generated_fiches(user_id);
