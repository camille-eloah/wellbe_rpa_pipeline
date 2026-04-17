-- Template de dump final (sera substituido/gerado automaticamente em runtime)
-- Arquivos reais: sql/movies_dump_YYYYMMDD_HHMMSS.sql
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_movies_name (name)
);

-- INSERT INTO movies (name, description) VALUES ('Movie Name', 'Movie Description')
-- ON DUPLICATE KEY UPDATE description = VALUES(description);
