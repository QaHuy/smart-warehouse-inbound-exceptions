-- Synthetic master data only. No person, customer, order, company, or real device data.
INSERT INTO sku (sku_id, barcode, name, description, is_active, compatibility_key) VALUES
    ('SKU-DEMO-A', 'SIMSKU0001', 'Demo ambient item A', 'Synthetic active SKU for ambient storage.', 1, 'AMBIENT'),
    ('SKU-DEMO-B', 'SIMSKU0002', 'Demo ambient item B', 'Synthetic active SKU for ambient storage.', 1, 'AMBIENT'),
    ('SKU-DEMO-C', 'SIMSKU0003', 'Demo cool item C', 'Synthetic inactive SKU retained for validation examples.', 0, 'COOL');

INSERT INTO location (
    location_id, location_code, zone_code, zone_priority,
    compatibility_key, pallet_capacity, used_pallet_count
) VALUES
    ('LOC-DEMO-A01', 'A-01', 'ZONE-A', 1, 'AMBIENT', 2, 0),
    ('LOC-DEMO-A02', 'A-02', 'ZONE-A', 1, 'AMBIENT', 1, 1),
    ('LOC-DEMO-B01', 'B-01', 'ZONE-B', 2, 'AMBIENT', 3, 1),
    ('LOC-DEMO-B02', 'B-02', 'ZONE-B', 2, 'COOL', 2, 0);

INSERT INTO device (device_id, device_name, device_type, status) VALUES
    ('DEV-DEMO-CONV', 'Simulated inbound conveyor', 'conveyor', 'online'),
    ('DEV-DEMO-LIFT', 'Simulated putaway lift', 'lift', 'online'),
    ('DEV-DEMO-ROBOT', 'Simulated transfer robot', 'robot', 'offline');
