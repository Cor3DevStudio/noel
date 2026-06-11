-- Migration V2 – PhilHealth case rates, SOA, and charge audit
-- Run this on existing clinic_management databases to add the new columns/tables.

USE clinic_management;

-- ── philhealth_records: add case_type, explicit HFF, PF columns ──────────────
ALTER TABLE philhealth_records
    ADD COLUMN IF NOT EXISTS case_type ENUM('Medical','Surgical') DEFAULT 'Medical' AFTER case_description,
    ADD COLUMN IF NOT EXISTS health_facility_fee DECIMAL(12,2) DEFAULT 0.00 AFTER case_rate,
    ADD COLUMN IF NOT EXISTS professional_fee_amount DECIMAL(12,2) DEFAULT 0.00 AFTER health_facility_fee;

-- Back-fill health_facility_fee / professional_fee_amount from pct columns
UPDATE philhealth_records
SET
    health_facility_fee    = ROUND(case_rate * hospital_share_pct / 100, 2),
    professional_fee_amount = ROUND(case_rate * professional_fee_pct / 100, 2)
WHERE health_facility_fee = 0;

-- ── billing_items: add encoded_by / updated_by ────────────────────────────────
ALTER TABLE billing_items
    ADD COLUMN IF NOT EXISTS encoded_by INT DEFAULT NULL AFTER medicine_id,
    ADD COLUMN IF NOT EXISTS updated_by INT DEFAULT NULL AFTER encoded_by,
    ADD COLUMN IF NOT EXISTS encoded_at DATETIME DEFAULT CURRENT_TIMESTAMP AFTER updated_by,
    ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER encoded_at;

ALTER TABLE billing_items
    ADD CONSTRAINT IF NOT EXISTS fk_bi_encoded_by FOREIGN KEY (encoded_by) REFERENCES users(id),
    ADD CONSTRAINT IF NOT EXISTS fk_bi_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- ── billings: add soa_number, philhealth_case_rate_id ─────────────────────────
ALTER TABLE billings
    ADD COLUMN IF NOT EXISTS soa_number VARCHAR(30) DEFAULT NULL AFTER billing_number,
    ADD COLUMN IF NOT EXISTS philhealth_case_rate_id INT DEFAULT NULL AFTER philhealth_deduction;

ALTER TABLE billings
    ADD CONSTRAINT IF NOT EXISTS fk_b_ph_case_rate FOREIGN KEY (philhealth_case_rate_id) REFERENCES philhealth_records(id);

-- ── charge_edit_log table ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS charge_edit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT NOT NULL,
    billing_item_id INT,
    action ENUM('ENCODE','EDIT','DELETE') NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    performed_by INT NOT NULL,
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (billing_id)      REFERENCES billings(id),
    FOREIGN KEY (billing_item_id) REFERENCES billing_items(id),
    FOREIGN KEY (performed_by)    REFERENCES users(id),
    INDEX idx_cel_billing  (billing_id),
    INDEX idx_cel_user     (performed_by),
    INDEX idx_cel_date     (performed_at)
) ENGINE=InnoDB;

-- ── indexes for philhealth_records lookup ─────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ph_case_type ON philhealth_records(case_type);
