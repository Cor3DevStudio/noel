-- Clinic Management System Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS clinic_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE clinic_management;

-- Roles
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    permissions JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),
    is_active TINYINT(1) DEFAULT 1,
    permissions JSON,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB;

-- Patients
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    birth_date DATE,
    gender ENUM('Male', 'Female', 'Other') DEFAULT 'Other',
    civil_status VARCHAR(30),
    contact_number VARCHAR(20),
    email VARCHAR(150),
    address_street VARCHAR(255),
    address_barangay VARCHAR(100),
    address_city VARCHAR(100),
    address_province VARCHAR(100),
    address_zip VARCHAR(10),
    emergency_contact_name VARCHAR(150),
    emergency_contact_relationship VARCHAR(50),
    emergency_contact_phone VARCHAR(20),
    philhealth_number VARCHAR(30),
    philhealth_category VARCHAR(50),
    philhealth_member_type VARCHAR(50),
    is_senior_citizen TINYINT(1) DEFAULT 0,
    senior_id_number VARCHAR(50),
    is_pwd TINYINT(1) DEFAULT 0,
    pwd_id_number VARCHAR(50),
    photo_path VARCHAR(500),
    notes TEXT,
    is_archived TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_name (last_name, first_name),
    INDEX idx_patient_number (patient_number)
) ENGINE=InnoDB;

-- Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason VARCHAR(255),
    status ENUM('Scheduled', 'Confirmed', 'Completed', 'Cancelled', 'No Show') DEFAULT 'Scheduled',
    notes TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_appointment_date (appointment_date)
) ENGINE=InnoDB;

-- Consultations
CREATE TABLE IF NOT EXISTS consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT,
    consultation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    chief_complaint TEXT,
    vital_signs JSON,
    diagnosis TEXT,
    treatment_plan TEXT,
    doctor_notes TEXT,
    follow_up_date DATE,
    status ENUM('In Progress', 'Completed', 'Cancelled') DEFAULT 'In Progress',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
) ENGINE=InnoDB;

-- Prescriptions
CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consultation_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    prescription_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    doctor_signature VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- Prescription Items
CREATE TABLE IF NOT EXISTS prescription_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_id INT,
    medicine_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    quantity INT DEFAULT 1,
    instructions TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Medicine Categories
CREATE TABLE IF NOT EXISTS medicine_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150),
    phone VARCHAR(20),
    email VARCHAR(150),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Medicines
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    supplier_id INT,
    generic_name VARCHAR(200) NOT NULL,
    brand_name VARCHAR(200),
    dosage_form VARCHAR(100),
    strength VARCHAR(100),
    unit_price DECIMAL(10, 2) DEFAULT 0.00,
    selling_price DECIMAL(10, 2) DEFAULT 0.00,
    price_effective_date DATE,
    stock_quantity INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    batch_number VARCHAR(50),
    expiration_date DATE,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES medicine_categories(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    INDEX idx_medicine_name (generic_name)
) ENGINE=InnoDB;

-- Inventory Transactions
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    transaction_type ENUM('Stock In', 'Stock Out', 'Adjustment', 'Dispensed') NOT NULL,
    quantity INT NOT NULL,
    batch_number VARCHAR(50),
    expiration_date DATE,
    unit_cost DECIMAL(10, 2),
    reference_number VARCHAR(50),
    notes TEXT,
    performed_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id),
    FOREIGN KEY (performed_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- Billings
CREATE TABLE IF NOT EXISTS billings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_number VARCHAR(30) NOT NULL UNIQUE,
    soa_number VARCHAR(30),
    soa_xml_path VARCHAR(500),
    patient_id INT NOT NULL,
    consultation_id INT,
    subtotal DECIMAL(12, 2) DEFAULT 0.00,
    discount_amount DECIMAL(12, 2) DEFAULT 0.00,
    discount_type VARCHAR(30),
    philhealth_deduction DECIMAL(12, 2) DEFAULT 0.00,
    philhealth_case_rate_id INT,
    ph_snapshot_case_code VARCHAR(20),
    ph_snapshot_case_description VARCHAR(255),
    ph_snapshot_case_type VARCHAR(20),
    ph_snapshot_case_rate DECIMAL(12, 2),
    ph_snapshot_hff DECIMAL(12, 2),
    ph_snapshot_pf DECIMAL(12, 2),
    ph_snapshot_effective_date DATE,
    total_amount DECIMAL(12, 2) DEFAULT 0.00,
    amount_paid DECIMAL(12, 2) DEFAULT 0.00,
    balance DECIMAL(12, 2) DEFAULT 0.00,
    payment_status ENUM('Unpaid', 'Partial', 'Paid', 'Cancelled') DEFAULT 'Unpaid',
    notes TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (consultation_id) REFERENCES consultations(id),
    FOREIGN KEY (philhealth_case_rate_id) REFERENCES philhealth_records(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- Billing Items
CREATE TABLE IF NOT EXISTS billing_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT NOT NULL,
    item_type ENUM('Consultation', 'Medicine', 'Procedure', 'Other') NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10, 2) DEFAULT 0.00,
    total_price DECIMAL(10, 2) DEFAULT 0.00,
    price_as_of DATE,
    medicine_id INT,
    encoded_by INT,
    updated_by INT,
    encoded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (billing_id) REFERENCES billings(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id),
    FOREIGN KEY (encoded_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    payment_method ENUM('Cash', 'Check', 'Bank Transfer', 'GCash', 'Other') DEFAULT 'Cash',
    receipt_number VARCHAR(50),
    notes TEXT,
    received_by INT,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (billing_id) REFERENCES billings(id),
    FOREIGN KEY (received_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- PhilHealth Case Rates
CREATE TABLE IF NOT EXISTS philhealth_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_code VARCHAR(20) NOT NULL UNIQUE,
    case_description VARCHAR(255) NOT NULL,
    case_type ENUM('Medical', 'Surgical') DEFAULT 'Medical',
    case_rate DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    health_facility_fee DECIMAL(12, 2) DEFAULT 0.00,
    professional_fee_amount DECIMAL(12, 2) DEFAULT 0.00,
    price_effective_date DATE,
    hospital_share_pct DECIMAL(5, 2) DEFAULT 70.00,
    professional_fee_pct DECIMAL(5, 2) DEFAULT 30.00,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ph_case_type (case_type),
    INDEX idx_ph_case_code (case_code)
) ENGINE=InnoDB;

-- PhilHealth Transactions
CREATE TABLE IF NOT EXISTS philhealth_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    billing_id INT,
    consultation_id INT,
    case_rate_id INT NOT NULL,
    philhealth_number VARCHAR(30),
    case_rate_amount DECIMAL(12, 2) DEFAULT 0.00,
    hospital_share DECIMAL(12, 2) DEFAULT 0.00,
    professional_fee DECIMAL(12, 2) DEFAULT 0.00,
    philhealth_deduction DECIMAL(12, 2) DEFAULT 0.00,
    patient_balance DECIMAL(12, 2) DEFAULT 0.00,
    senior_discount DECIMAL(12, 2) DEFAULT 0.00,
    pwd_discount DECIMAL(12, 2) DEFAULT 0.00,
    total_bill DECIMAL(12, 2) DEFAULT 0.00,
    notes TEXT,
    processed_by INT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (billing_id) REFERENCES billings(id),
    FOREIGN KEY (consultation_id) REFERENCES consultations(id),
    FOREIGN KEY (case_rate_id) REFERENCES philhealth_records(id),
    FOREIGN KEY (processed_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- PhilHealth Claim Forms (CF2, CF3, CF4, CF5)
CREATE TABLE IF NOT EXISTS philhealth_claim_forms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    form_number VARCHAR(30) NOT NULL UNIQUE,
    form_type ENUM('CF2', 'CF3', 'CF4', 'CF5') NOT NULL,
    status ENUM('Draft', 'Submitted', 'Approved', 'Rejected') DEFAULT 'Draft',
    patient_id INT NOT NULL,
    transaction_id INT,

    -- Common fields
    philhealth_number VARCHAR(30),
    date_of_claim DATE,
    diagnosis VARCHAR(500),
    icd_code VARCHAR(50),
    case_rate_code VARCHAR(50),
    total_amount_claimed DECIMAL(12, 2) DEFAULT 0.00,

    -- CF2 / CF4 – Facility/Hospital fields
    admission_date DATE,
    discharge_date DATE,
    type_of_admission VARCHAR(50),
    room_charges DECIMAL(12, 2) DEFAULT 0.00,
    medicine_charges DECIMAL(12, 2) DEFAULT 0.00,
    xray_lab_charges DECIMAL(12, 2) DEFAULT 0.00,
    other_charges DECIMAL(12, 2) DEFAULT 0.00,
    hospital_share DECIMAL(12, 2) DEFAULT 0.00,

    -- CF3 – Professional Fee fields
    physician_name VARCHAR(150),
    physician_prc_no VARCHAR(50),
    physician_ptr_no VARCHAR(50),
    physician_philhealth_no VARCHAR(30),
    type_of_claim VARCHAR(50),
    professional_fee_claimed DECIMAL(12, 2) DEFAULT 0.00,
    professional_fee_share DECIMAL(12, 2) DEFAULT 0.00,

    -- CF5 – ESRD / Dialysis fields
    dialysis_center_name VARCHAR(200),
    dialysis_center_accreditation VARCHAR(50),
    period_from DATE,
    period_to DATE,
    number_of_sessions INT,
    dialysis_type VARCHAR(50),

    notes TEXT,
    prepared_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (transaction_id) REFERENCES philhealth_transactions(id),
    FOREIGN KEY (prepared_by) REFERENCES users(id),
    INDEX idx_cf_form_type (form_type),
    INDEX idx_cf_patient (patient_id),
    INDEX idx_cf_status (status)
) ENGINE=InnoDB;

-- Clinic Settings
CREATE TABLE IF NOT EXISTS clinic_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clinic_name VARCHAR(200) DEFAULT 'Hospital Management System',
    clinic_address TEXT,
    clinic_phone VARCHAR(50),
    clinic_email VARCHAR(150),
    clinic_logo_path VARCHAR(500),
    receipt_header TEXT,
    receipt_footer TEXT,
    consultation_fee DECIMAL(10, 2) DEFAULT 500.00,
    consultation_fee_effective_date DATE,
    tax_id VARCHAR(50),
    philhealth_accreditation VARCHAR(50),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Charge Edit Log (tracks who encodes/edits billing charges)
CREATE TABLE IF NOT EXISTS charge_edit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT NOT NULL,
    billing_item_id INT,
    action ENUM('ENCODE', 'EDIT', 'DELETE') NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    performed_by INT NOT NULL,
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (billing_id) REFERENCES billings(id),
    FOREIGN KEY (billing_item_id) REFERENCES billing_items(id),
    FOREIGN KEY (performed_by) REFERENCES users(id),
    INDEX idx_cel_billing (billing_id),
    INDEX idx_cel_user (performed_by),
    INDEX idx_cel_date (performed_at)
) ENGINE=InnoDB;

-- Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(50),
    description TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_activity_date (created_at)
) ENGINE=InnoDB;

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    action ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
    old_values JSON,
    new_values JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_audit_date (created_at)
) ENGINE=InnoDB;
