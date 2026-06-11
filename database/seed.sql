-- Sample PhilHealth Case Rates
USE clinic_management;

INSERT IGNORE INTO philhealth_records (case_code, case_description, case_rate, hospital_share_pct, professional_fee_pct) VALUES
('ACR001', 'Acute Gastroenteritis', 6000.00, 70.00, 30.00),
('PN001', 'Community Acquired Pneumonia', 15000.00, 70.00, 30.00),
('UTI001', 'Urinary Tract Infection', 6000.00, 70.00, 30.00),
('HTN001', 'Hypertension Package', 9000.00, 70.00, 30.00),
('DM001', 'Diabetes Mellitus Package', 9000.00, 70.00, 30.00);

-- Default clinic settings
INSERT IGNORE INTO clinic_settings (id, clinic_name, consultation_fee, receipt_footer) VALUES
(1, 'Sample Community Clinic', 500.00, 'Thank you for choosing our clinic!');
