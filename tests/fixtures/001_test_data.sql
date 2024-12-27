-- Insert test counties
INSERT INTO county_info (id, name, state, abbreviation) VALUES
(1, 'Cobb', 'GA', 'COB'),
(2, 'Clayton', 'GA', 'CLA');

-- Insert source publications
INSERT INTO source_publication (county_id, platform_name, platform_url, data_format) VALUES
(1, 'Cobb County Tax Sales', 'https://cobbcounty.org/tax-sales', 'PDF'),
(2, 'Clayton County Tax Sales PDF', 'https://claytoncountyga.gov/tax-sales', 'PDF'),
(2, 'Clayton County Tax Sales Excel', 'https://claytoncountyga.gov/tax-sales', 'EXCEL');

-- Insert publication schedules
INSERT INTO publication_schedule (county_id, days_before_sale, publication_type, legal_newspaper, additional_requirements) VALUES
(1, 30, 'Legal Notice', 'Marietta Daily Journal', 'Must publish in legal organ for 4 consecutive weeks'),
(2, 30, 'Legal Notice', 'Clayton News Daily', 'Must publish in legal organ for 4 consecutive weeks');
