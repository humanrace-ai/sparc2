-- Create property history audit table
CREATE TABLE property_history (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100)
);

-- Create indexes for property history
CREATE INDEX idx_property_changes ON property_history(property_id);
CREATE INDEX idx_change_date ON property_history(changed_at);

-- Create sale status history audit table
CREATE TABLE sale_status_history (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sale_history(id),
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100),
    notes TEXT
);

-- Create index for sale status history
CREATE INDEX idx_sale_status ON sale_status_history(sale_id);
