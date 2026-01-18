CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    brand TEXT,
    description TEXT,
    image_url TEXT
);

CREATE TABLE offers (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    website_name TEXT NOT NULL,
    price NUMERIC(10,2),
    url TEXT,
    rating NUMERIC(3,2),
    reviews_count TEXT
);

CREATE TABLE attributes (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attribute_name TEXT NOT NULL,
    attribute_value TEXT
);

CREATE INDEX idx_products_name ON products(canonical_name);
CREATE INDEX idx_offers_price ON offers(price);
