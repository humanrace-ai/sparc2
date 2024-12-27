-- Create source_publication table
CREATE TABLE source_publication (
    id SERIAL PRIMARY KEY,
    county_id INTEGER NOT NULL REFERENCES county_info(id),
    platform_name VARCHAR(100) NOT NULL,
    platform_url VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    data_format VARCHAR(50),
    historical_data_from DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_county_source_pub
        FOREIGN KEY (county_id)
        REFERENCES county_info(id)
        ON DELETE CASCADE
);

-- Create index on county_id and platform_name
CREATE INDEX idx_source_pub_county_platform 
ON source_publication(county_id, platform_name);

-- Create publication_schedule table
CREATE TABLE publication_schedule (
    id SERIAL PRIMARY KEY,
    county_id INTEGER NOT NULL REFERENCES county_info(id),
    days_before_sale INTEGER NOT NULL,
    publication_type VARCHAR(50) NOT NULL,
    legal_newspaper VARCHAR(255),
    additional_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_county_pub_schedule
        FOREIGN KEY (county_id)
        REFERENCES county_info(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_days_before_sale
        CHECK (days_before_sale > 0)
);

-- Create index on county_id
CREATE INDEX idx_pub_schedule_county 
ON publication_schedule(county_id);

-- Add triggers to update modified_at timestamp
CREATE OR REPLACE FUNCTION update_modified_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_source_publication_modtime
    BEFORE UPDATE ON source_publication
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_at_column();

CREATE TRIGGER update_publication_schedule_modtime
    BEFORE UPDATE ON publication_schedule
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_at_column();
