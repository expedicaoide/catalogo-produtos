-- ==========================================
-- BANCO DE DADOS - CATALOGO DE MOTOS
-- ==========================================

-- EXCLUIR TABELAS EXISTENTES
DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS categoria;
DROP TABLE IF EXISTS usuario;


-- ==========================================
-- TABELA: CATEGORIA
-- Cadastro de marcas de motocicletas
-- ==========================================

CREATE TABLE categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT 1,
    imagem BLOB,
    img VARCHAR(255)
);


-- ==========================================
-- TABELA: PRODUTO
-- Cadastro das motocicletas
-- ==========================================

CREATE TABLE produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nome VARCHAR(100) NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(100),

    ano_fabricacao INTEGER,
    ano_modelo INTEGER,

    cilindrada INTEGER,
    quilometragem INTEGER,

    cor VARCHAR(30),
    combustivel VARCHAR(30),
    cambio VARCHAR(30),

    preco DECIMAL(10,2),

    descricao TEXT,

    status VARCHAR(20) DEFAULT 'Disponível',

    ativo BOOLEAN DEFAULT 1,

    imagem BLOB,
    img VARCHAR(255),

    id_categoria INTEGER,

    FOREIGN KEY (id_categoria)
    REFERENCES categoria(id)
);


-- ==========================================
-- TABELA: USUARIO
-- Acesso ao sistema
-- ==========================================

CREATE TABLE usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nome VARCHAR(100) NOT NULL,

    senha VARCHAR(255) NOT NULL,

    ativo BOOLEAN DEFAULT 1
);


-- ==========================================
-- CADASTRO INICIAL DE MARCAS
-- ==========================================

INSERT INTO categoria (nome, descricao, ativo)
VALUES
    ('Honda', 'Motocicletas da marca Honda', 1),
    ('Yamaha', 'Motocicletas da marca Yamaha', 1),
    ('Suzuki', 'Motocicletas da marca Suzuki', 1),
    ('Kawasaki', 'Motocicletas da marca Kawasaki', 1),
    ('BMW', 'Motocicletas da marca BMW', 1),
    ('Triumph', 'Motocicletas da marca Triumph', 1),
    ('Dafra', 'Motocicletas da marca Dafra', 1),
    ('Royal Enfield', 'Motocicletas da marca Royal Enfield', 1),
    ('Shineray', 'Motocicletas da marca Shineray', 1),
    ('Outras', 'Outras marcas de motocicletas', 1);


-- ==========================================
-- FINALIZADO
-- ==========================================