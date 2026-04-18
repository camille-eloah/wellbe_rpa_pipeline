
-- Script de criação do banco de dados
CREATE DATABASE IF NOT EXISTS db_wellbe_movies
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_wellbe_movies;

-- Script de criacao da tabela principal
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_movies_name (name)
);
