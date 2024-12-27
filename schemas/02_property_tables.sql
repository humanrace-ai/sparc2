-- Property table for storing detailed property information
CREATE TABLE property (
  id SERIAL PRIMARY KEY,
  county_id INTEGER NOT NULL REFERENCES county_info(id),
  parcel_id VARCHAR(100) NOT NULL,
  street_address VARCHAR(255),
  city VARCHAR(100),
  zip_code VARCHAR(10),
  current_owner VARCHAR(255),
  market_value DECIMAL(12,2),
  assessed_value DECIMAL(12,2),
  taxes_due DECIMAL(12,2),
  property_class VARCHAR(50),
  land_use VARCHAR(100),
  acreage DECIMAL(10,2),
  year_built INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(county_id, parcel_id)
);

-- Indexes for property table
CREATE INDEX idx_property_location ON property(county_id, city, zip_code);
CREATE INDEX idx_parcel ON property(county_id, parcel_id);

-- Sale history table for tracking property sales
CREATE TABLE sale_history (
  id SERIAL PRIMARY KEY,
  property_id INTEGER NOT NULL REFERENCES property(id),
  sale_list_id INTEGER NOT NULL REFERENCES tax_sale_list(id),
  sale_date DATE NOT NULL,
  sale_price DECIMAL(12,2),
  buyer_name VARCHAR(255),
  sale_status VARCHAR(50) NOT NULL,
  redemption_deadline DATE,
  redeemed BOOLEAN DEFAULT FALSE,
  deed_recording_info VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sale_history table
CREATE INDEX idx_property_sales ON sale_history(property_id);
CREATE INDEX idx_sale_list ON sale_history(sale_list_id);
CREATE INDEX idx_sale_date ON sale_history(sale_date);
