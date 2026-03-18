CREATE DATABASE production_db ENCODING 'UTF8';
\c production_db

CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    inn VARCHAR(12),
    address TEXT,
    phone VARCHAR(20),
    isSalesman BOOLEAN DEFAULT FALSE,
    isBuyer BOOLEAN DEFAULT TRUE
);

CREATE TABLE production (
    id SERIAL PRIMARY KEY,
    prod_number VARCHAR(50) NOT NULL UNIQUE,
    prod_date DATE NOT NULL DEFAULT CURRENT_DATE,
    p_type INTEGER NOT NULL REFERENCES types(id)
);

CREATE TABLE nomenclature (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    n_type INTEGER NOT NULL REFERENCES types(id),
    unit INTEGER NOT NULL REFERENCES units(id),
    code VARCHAR(50) UNIQUE
);

CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    nomenc_id INTEGER NOT NULL REFERENCES nomenclature(id) ON DELETE CASCADE,
    price NUMERIC(15, 2) NOT NULL CHECK (price >= 0),
    price_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE specifications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    nomenc_id INTEGER NOT NULL REFERENCES nomenclature(id),
    amount NUMERIC(15, 3) NOT NULL DEFAULT 1 CHECK (amount > 0)
);

CREATE TABLE spec_materials (
    id SERIAL PRIMARY KEY,
    spec_id INTEGER NOT NULL REFERENCES specifications(id) ON DELETE CASCADE,
    nomenc_id INTEGER NOT NULL REFERENCES nomenclature(id),
    amount NUMERIC(15, 3) NOT NULL CHECK (amount > 0),
    unit INTEGER NOT NULL REFERENCES units(id)
);

CREATE TABLE released_prod (
    id SERIAL PRIMARY KEY,
    prod_id INTEGER NOT NULL REFERENCES production(id) ON DELETE CASCADE,
    nomenc_id INTEGER NOT NULL REFERENCES nomenclature(id),
    spec_id INTEGER REFERENCES specifications(id),
    amount NUMERIC(15, 3) NOT NULL CHECK (amount > 0)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    executor VARCHAR(150),
    customer INTEGER NOT NULL REFERENCES customers(id)
);

CREATE TABLE order_list (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    nomenc_id INTEGER NOT NULL REFERENCES nomenclature(id),
    amount NUMERIC(15, 3) NOT NULL CHECK (amount > 0),
    price NUMERIC(15, 2) NOT NULL
);