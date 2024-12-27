CREATE TABLE county_info (
  id SERIAL PRIMARY KEY,
  county_name VARCHAR(100) NOT NULL UNIQUE,
  contact_email VARCHAR(255),
  contact_phone VARCHAR(20),
  website_url VARCHAR(255),
  sale_location VARCHAR(255),
  sale_frequency VARCHAR(50),
  registration_requirements TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_county_name ON county_info(county_name);

CREATE TABLE tax_sale_list (
  id SERIAL PRIMARY KEY,
  county_id INTEGER NOT NULL REFERENCES county_info(id),
  sale_date DATE NOT NULL,
  publication_date DATE NOT NULL,
  list_status VARCHAR(50) NOT NULL,
  total_properties INTEGER,
  source_platform VARCHAR(100),
  source_url VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT valid_dates CHECK (publication_date < sale_date)
);

CREATE INDEX idx_sale_date ON tax_sale_list(sale_date);
CREATE INDEX idx_county_sale ON tax_sale_list(county_id, sale_date);
