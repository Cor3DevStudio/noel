# User Manual

## Getting Started

### Logging In

1. Launch the application with `python main.py`
2. Enter your username and password
3. Click **Sign In**

Your role determines which modules appear in the sidebar.

---

## Dashboard

The dashboard shows:
- Total registered patients
- Today's appointments and consultations
- Today's and monthly revenue
- Low stock and expiring medicine alerts
- Recent patients list

Click **Refresh** by navigating away and back to update statistics.

---

## Patient Management

### Register a New Patient

1. Go to **Patients**
2. Click **New Patient**
3. Fill in required fields (First Name, Last Name)
4. Add PhilHealth, senior citizen, or PWD information as applicable
5. Click **Save Patient**

### Search Patients

Use the search bar to find patients by name, patient number, PhilHealth number, or contact.

### Archive a Patient

Select a patient from the list, then click **Archive**. Archived patients are hidden from default search results.

---

## Appointments

1. Go to **Appointments**
2. Select patient, doctor, date, and time
3. Enter reason and status
4. Click **Save**

Use the date filter and **Load Schedule** to view appointments for a specific day.

To cancel: select the appointment and click **Cancel Appt**.

---

## Consultations

1. Go to **Consultations**
2. Select a patient
3. Enter chief complaint, vital signs, diagnosis, and treatment plan
4. Click **Save Consultation**
5. Click **Complete** when finished

Use **Load History** to view past consultations for the selected patient.

---

## Medicine Inventory

### Add Medicine

Click **Add Medicine** and fill in generic name, brand, price, and initial stock.

### Stock In / Stock Out

1. Click a medicine row to select it
2. Enter quantity
3. Click **Stock In** or **Stock Out**

Low stock items appear on the dashboard when quantity falls below the reorder level.

---

## Billing

1. Go to **Billing**
2. Select a patient
3. Click **Add Consultation Fee** or **Add Item** for additional charges
4. Click **Create Bill**
5. Enter payment amount and method
6. Click **Record Payment**

Senior citizens and PWD patients receive an automatic 20% discount.

---

## PhilHealth

1. Go to **PhilHealth**
2. Select patient (must have PhilHealth number on file)
3. Select case rate
4. Enter total bill amount
5. Click **Compute Benefits** to preview
6. Click **Process Transaction** to save

The summary shows hospital share, professional fee, deductions, and patient balance.

---

## Reports

1. Go to **Reports**
2. Set date range if applicable
3. Click **PDF** or **Excel** on the desired report type
4. Choose save location

Available reports: income, patients, consultations, inventory, low stock, expiring medicines, billing, PhilHealth.

---

## Settings

### Clinic Info
Update clinic name, address, phone, consultation fee, and receipt header/footer.

### Users (Administrator only)
Add staff accounts and assign roles.

### Backup & Restore
- **Backup Database** — saves a `.sql` file to the `backups/` folder
- **Restore Database** — loads a previously saved backup

### My Account
Change your username or password.

---

## Default Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |

Change the default password immediately after first login.
