"""PhilHealth benefit computation, claim forms and eClaims transmission view."""

import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from tkinter import filedialog
from typing import Optional
import tkinter as tk

import customtkinter as ctk

from config.settings import ECLAIMS_DIR
from reports.pdf_generator import PDFGenerator
from services.philhealth_service import (
    ECLAIM_DOCUMENT_TYPES,
    guess_eclaim_document_type,
    normalize_supporting_docs,
)
from utils.helpers import format_currency, format_date, format_datetime, format_price_as_of
from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, SearchPickerField, show_message

_STATUS_COLORS = {
    "Draft":       "#6B7280",
    "Submitted":   "#2563EB",
    "Approved":    "#16A34A",
    "Rejected":    "#DC2626",
}

FORM_TYPE_LABELS = {
    "CF1": "CF1 – Member Information Form",
    "CF2": "CF2 – Hospital / Facility Claim",
    "CF3": "CF3 – Clinical Record",
    "CF4": "CF4 – All Case Rates / Outpatient",
    "CF5": "CF5 – ESRD / Dialysis",
    "CSF": "CSF – Claim Signature Form",
}

ECLAIM_STATUS_COLORS = {
    "Pending":      "#6B7280",
    "Transmitted":  "#2563EB",
    "Acknowledged": "#16A34A",
    "Rejected":     "#DC2626",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Shared dialog helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_dialog(master, title: str, w: int = 860, h: int = 700) -> ctk.CTkToplevel:
    dlg = ctk.CTkToplevel(master)
    dlg.title(title)
    dlg.geometry(f"{w}x{h}")
    dlg.resizable(True, True)
    dlg.grab_set()
    dlg.configure(fg_color=Theme.PAGE_BG)
    dlg.grid_columnconfigure(0, weight=1)
    dlg.grid_rowconfigure(1, weight=1)
    return dlg


def _section_hdr(parent, text: str, grid_row: int, col: int = 0, span: int = 2) -> None:
    fr = ctk.CTkFrame(parent, fg_color=Theme.SECONDARY, corner_radius=6, height=30)
    fr.grid(row=grid_row, column=col, columnspan=span, sticky="ew", padx=4, pady=(12, 2))
    fr.pack_propagate(False)
    ctk.CTkLabel(fr, text=f"  {text}", font=Theme.FONT_SUBHEADING,
                 text_color=Theme.TEXT_PRIMARY, anchor="w").pack(fill="both", expand=True)


def _field(parent, label: str, label_row: int, col: int, widget_type: str = "entry",
           values: list = None, default: str = "", width: int = 1,
           height: int = 36) -> ctk.CTkEntry | ctk.CTkComboBox | ctk.CTkTextbox:
    ctk.CTkLabel(parent, text=label, font=Theme.FONT_SMALL,
                 text_color=Theme.TEXT_SECONDARY, anchor="w"
                 ).grid(row=label_row, column=col, columnspan=width,
                        sticky="w", padx=10, pady=(6, 1))
    if widget_type == "combo":
        w = ctk.CTkComboBox(parent, values=values or [], height=height,
                            font=Theme.FONT_BODY, corner_radius=6,
                            border_color=Theme.BORDER, state="readonly")
        if values:
            w.set(values[0])
    elif widget_type == "text":
        w = ctk.CTkTextbox(parent, height=height, font=Theme.FONT_BODY,
                           corner_radius=6, border_color=Theme.BORDER, border_width=1)
    else:
        w = ctk.CTkEntry(parent, height=height, font=Theme.FONT_BODY,
                         corner_radius=6, border_color=Theme.BORDER)
    w.grid(row=label_row + 1, column=col, columnspan=width,
           sticky="ew", padx=10, pady=(0, 2))
    if default:
        if isinstance(w, ctk.CTkTextbox):
            w.insert("1.0", default)
        elif isinstance(w, ctk.CTkComboBox):
            w.set(default)
        else:
            w.insert(0, default)
    return w


def _field_row_advance(*widgets) -> int:
    """Grid rows consumed by a field group (label row + widget row + tall text areas)."""
    extra = 0
    for w in widgets:
        if isinstance(w, ctk.CTkTextbox):
            h = int(w.cget("height"))
            if h > 44:
                extra = max(extra, (h - 36 + 23) // 24)
    return 2 + extra


def _get(w) -> str:
    if isinstance(w, ctk.CTkTextbox):
        return w.get("1.0", "end-1c").strip()
    return w.get().strip()


def _parse_date(s: str):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return date.today()


def _dialog_footer(dlg, on_save) -> None:
    fr = ctk.CTkFrame(dlg, fg_color=Theme.PRIMARY, height=56, corner_radius=0)
    fr.grid(row=2, column=0, sticky="ew")
    fr.grid_propagate(False)
    fr.grid_columnconfigure(0, weight=1)
    ActionButton(fr, text="Save Claim Form", style="success",
                 command=on_save).grid(row=0, column=0, sticky="e",
                                       padx=(0, 10), pady=8)
    ActionButton(fr, text="Cancel", style="secondary",
                 command=dlg.destroy).grid(row=0, column=1, sticky="e",
                                           padx=(0, 20), pady=8)


def _dialog_banner(dlg, title: str, subtitle: str = "") -> None:
    hdr = ctk.CTkFrame(dlg, fg_color=Theme.ACCENT, corner_radius=0, height=58)
    hdr.grid(row=0, column=0, sticky="ew")
    hdr.grid_propagate(False)
    ctk.CTkLabel(hdr, text=title, font=Theme.FONT_HEADING,
                 text_color="white", anchor="w").pack(anchor="w", padx=20, pady=(10, 2))
    if subtitle:
        ctk.CTkLabel(hdr, text=subtitle, font=Theme.FONT_TINY,
                     text_color="#BFDBFE", anchor="w").pack(anchor="w", padx=20)


def _patient_id(combo: ctk.CTkComboBox) -> Optional[int]:
    try:
        return int(combo.get().split(" - ")[0])
    except (ValueError, IndexError):
        return None


def _save_form(dlg, service, form_type: str, data: dict, on_saved) -> None:
    if not data.get("patient_id"):
        show_message(dlg, "Validation", "Please select a patient.", "warning")
        return
    try:
        ok, msg, _ = service.create_claim_form(form_type, data)
    except Exception as exc:
        show_message(dlg, "Error", str(exc), "error")
        return
    if ok:
        on_saved()
        dlg.destroy()
    else:
        show_message(dlg, "Claim Form", msg, "error")


# ─────────────────────────────────────────────────────────────────────────────
#  CF1 – Member Information Form
# ─────────────────────────────────────────────────────────────────────────────

def _CF1Dialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CF1 – Member Information Form", w=820, h=620)
    _dialog_banner(dlg, "CF1 – Member Information Form",
                   "Republic of the Philippines  |  Philippine Health Insurance Corporation")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white",
                                    corner_radius=0, border_width=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2), weight=1)
    r = 0

    # ── Part I: Member Information ──────────────────────────────────────────
    _section_hdr(scroll, "PART I – MEMBER INFORMATION", r, span=3); r += 1
    pat_cb = _field(scroll, "Patient / Member *", r, 0, "combo",
                    patients or ["No patients"]); r += 2
    pin    = _field(scroll, "PhilHealth Identification No. (PIN)", r, 0)
    dob    = _field(scroll, "Date of Birth (YYYY-MM-DD)", r, 1)
    sex_cb = _field(scroll, "Sex", r, 2, "combo", ["Male", "Female"])
    r += _field_row_advance(pin, dob, sex_cb)
    addr   = _field(scroll, "Mailing Address", r, 0, width=3, height=36); r += 2
    land   = _field(scroll, "Landline No.", r, 0)
    mobile = _field(scroll, "Mobile No.", r, 1)
    email  = _field(scroll, "Email Address", r, 2)
    r += _field_row_advance(land, mobile, email)

    # ── Part II: Patient Information (if dependent) ─────────────────────────
    _section_hdr(scroll, "PART II – PATIENT INFORMATION (if patient is a dependent)", r, span=3); r += 1
    dep_pin  = _field(scroll, "PhilHealth Identification No. (PIN) of Dependent", r, 0)
    dep_name = _field(scroll, "Name of Patient (Last, First, Middle)", r, 1, width=2)
    r += _field_row_advance(dep_pin, dep_name)
    dep_rel  = _field(scroll, "Relationship to Member", r, 0, "combo",
                      ["— (Member is Patient)", "Child", "Parent", "Spouse"])
    dep_dob  = _field(scroll, "Date of Birth (YYYY-MM-DD)", r, 1)
    dep_sex  = _field(scroll, "Sex", r, 2, "combo", ["Male", "Female"])
    r += _field_row_advance(dep_rel, dep_dob, dep_sex)

    # ── Part IV: Employer ───────────────────────────────────────────────────
    _section_hdr(scroll, "PART IV – EMPLOYER'S CERTIFICATION (employed members only)", r, span=3); r += 1
    pen    = _field(scroll, "PhilHealth Employer No. (PEN)", r, 0)
    emp_tel= _field(scroll, "Contact No.", r, 1)
    emp_nm = _field(scroll, "Business Name of Employer", r, 2)
    r += _field_row_advance(pen, emp_tel, emp_nm)
    notes  = _field(scroll, "Notes / Remarks", r, 0, "text", height=50, width=3)
    r += _field_row_advance(notes)

    def _save():
        pid = _patient_id(pat_cb)
        _save_form(dlg, service, "CF1", {
            "patient_id": pid,
            "philhealth_number": _get(pin),
            "diagnosis": _get(dep_name) or "—",
            "icd_code": _get(dep_rel),
            "notes": (
                f"DOB:{_get(dob)} SEX:{_get(sex_cb)} ADDR:{_get(addr)} "
                f"LAND:{_get(land)} MOB:{_get(mobile)} EMAIL:{_get(email)} "
                f"DEP_PIN:{_get(dep_pin)} DEP_DOB:{_get(dep_dob)} DEP_SEX:{_get(dep_sex)} "
                f"PEN:{_get(pen)} EMPTEL:{_get(emp_tel)} EMPNM:{_get(emp_nm)} "
                f"NOTES:{_get(notes)}"
            ),
            "total_amount_claimed": 0,
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  CF2 – Hospital / Facility Claim Form
# ─────────────────────────────────────────────────────────────────────────────

def _CF2Dialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CF2 – Hospital / Facility Claim Form", w=920, h=760)
    _dialog_banner(dlg, "CF2 – Hospital / Facility Claim Form",
                   "Republic of the Philippines  |  Philippine Health Insurance Corporation  |  Revised September 2018")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white", corner_radius=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
    r = 0

    # ── Part I: HCI Information ─────────────────────────────────────────────
    _section_hdr(scroll, "PART I – HEALTH CARE INSTITUTION (HCI) INFORMATION", r, span=4); r += 1
    pan   = _field(scroll, "PhilHealth Accreditation No. (PAN) of HCI", r, 0, width=2)
    hci_n = _field(scroll, "Name of Health Care Institution", r, 2, width=2)
    r += _field_row_advance(pan, hci_n)
    hci_a = _field(scroll, "Address of HCI", r, 0, width=4); r += 2

    # ── Part II: Patient Confinement ────────────────────────────────────────
    _section_hdr(scroll, "PART II – PATIENT CONFINEMENT INFORMATION", r, span=4); r += 1
    pat_cb = _field(scroll, "Patient *", r, 0, "combo", patients or ["No patients"], width=2)
    ph_num = _field(scroll, "PhilHealth No. (PIN)", r, 2)
    acc_tp = _field(scroll, "Type of Accommodation", r, 3, "combo",
                    ["Non-Private (Charity/Service)", "Private"])
    r += _field_row_advance(pat_cb, ph_num, acc_tp)

    ref_yn = _field(scroll, "Referred from another HCI?", r, 0, "combo", ["No", "Yes"])
    ref_nm = _field(scroll, "Name of Referring HCI", r, 1, width=3)
    r += _field_row_advance(ref_yn, ref_nm)

    d_adm  = _field(scroll, "Date Admitted (YYYY-MM-DD)", r, 0,
                    default=str(date.today()))
    t_adm  = _field(scroll, "Time Admitted (HH:MM AM/PM)", r, 1)
    d_dis  = _field(scroll, "Date Discharged (YYYY-MM-DD)", r, 2,
                    default=str(date.today()))
    t_dis  = _field(scroll, "Time Discharged (HH:MM AM/PM)", r, 3)
    r += _field_row_advance(d_adm, t_adm, d_dis, t_dis)

    disp   = _field(scroll, "Patient Disposition", r, 0, "combo",
                    ["Improved", "Recovered", "HAMA (Home Against Medical Advice)",
                     "Absconded", "Expired", "Transferred/Referred"])
    adm_tp = _field(scroll, "Type of Admission", r, 1, "combo",
                    ["Ordinary", "Emergency", "Day Surgery"])
    physn  = _field(scroll, "Attending Physician", r, 2, width=2)
    r += _field_row_advance(disp, adm_tp, physn)

    # ── Diagnoses ───────────────────────────────────────────────────────────
    _section_hdr(scroll, "ADMISSION & DISCHARGE DIAGNOSES", r, span=4); r += 1
    adm_dx = _field(scroll, "Admission Diagnosis/es", r, 0, "text",
                    height=44, width=4)
    r += _field_row_advance(adm_dx)
    dx1    = _field(scroll, "1st Discharge Diagnosis", r, 0, width=2)
    icd1   = _field(scroll, "ICD-10 Code", r, 2)
    rvs1   = _field(scroll, "RVS Code (Procedure)", r, 3)
    r += _field_row_advance(dx1, icd1, rvs1)
    dx2    = _field(scroll, "2nd Discharge Diagnosis (if any)", r, 0, width=2)
    icd2   = _field(scroll, "ICD-10 Code", r, 2)
    rvs2   = _field(scroll, "RVS Code (Procedure)", r, 3)
    r += _field_row_advance(dx2, icd2, rvs2)

    # ── PhilHealth Benefits ─────────────────────────────────────────────────
    _section_hdr(scroll, "PHILHEALTH BENEFITS", r, span=4); r += 1
    cr1    = _field(scroll, "1st Case Rate Code", r, 0, width=2)
    cr2    = _field(scroll, "2nd Case Rate Code (if applicable)", r, 2, width=2)
    r += _field_row_advance(cr1, cr2)

    # ── Charges ─────────────────────────────────────────────────────────────
    _section_hdr(scroll, "PART III – CHARGES & CONSUMPTION OF BENEFITS", r, span=4); r += 1
    total  = _field(scroll, "Total Amount Claimed (₱)", r, 0, default="0")
    room   = _field(scroll, "Room & Board Charges (₱)", r, 1, default="0")
    meds   = _field(scroll, "Medicine & Drug Charges (₱)", r, 2, default="0")
    xray   = _field(scroll, "X-Ray / Laboratory Charges (₱)", r, 3, default="0")
    r += _field_row_advance(total, room, meds, xray)
    oth    = _field(scroll, "Other Charges (₱)", r, 0, default="0")
    hsp    = _field(scroll, "Hospital Share / PhilHealth Benefit (₱)", r, 1, default="0")
    pf     = _field(scroll, "Total Professional Fees (₱)", r, 2, default="0")
    notes  = _field(scroll, "Notes / Remarks", r, 3)
    r += _field_row_advance(oth, hsp, pf, notes)

    def _save():
        pid = _patient_id(pat_cb)
        dx   = _get(dx1) or _get(adm_dx)
        _save_form(dlg, service, "CF2", {
            "patient_id":           pid,
            "philhealth_number":    _get(ph_num),
            "diagnosis":            dx,
            "icd_code":             _get(icd1),
            "case_rate_code":       _get(cr1),
            "second_case_rate_code": _get(cr2),
            "total_amount_claimed": _get(total) or "0",
            "admission_date":       _parse_date(_get(d_adm)),
            "discharge_date":       _parse_date(_get(d_dis)),
            "time_admitted":        _get(t_adm),
            "time_discharged":      _get(t_dis),
            "type_of_admission":    _get(adm_tp),
            "patient_disposition":  _get(disp),
            "accommodation_type":   _get(acc_tp),
            "admission_diagnosis":  _get(adm_dx),
            "referring_hci":        _get(ref_nm) if _get(ref_yn) == "Yes" else "",
            "attending_physician":  _get(physn),
            "room_charges":         _get(room) or "0",
            "medicine_charges":     _get(meds) or "0",
            "xray_lab_charges":     _get(xray) or "0",
            "other_charges":        _get(oth) or "0",
            "hospital_share":       _get(hsp) or "0",
            "notes":                (f"PAN:{_get(pan)} HCI:{_get(hci_n)} ADDR:{_get(hci_a)} "
                                     f"DX2:{_get(dx2)} ICD2:{_get(icd2)} RVS1:{_get(rvs1)} "
                                     f"RVS2:{_get(rvs2)} PF:{_get(pf)} {_get(notes)}"),
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  CF3 – Clinical Record
# ─────────────────────────────────────────────────────────────────────────────

def _CF3Dialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CF3 – Clinical Record", w=900, h=760)
    _dialog_banner(dlg, "CF3 – Clinical Record",
                   "Philippine Health Insurance Corporation  |  Revised November 2013")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white", corner_radius=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2), weight=1)
    r = 0

    # ── Part I: Patient's Clinical Record ───────────────────────────────────
    _section_hdr(scroll, "PART I – PATIENT'S CLINICAL RECORD", r, span=3); r += 1
    pan    = _field(scroll, "PhilHealth Accreditation No. (PAN) – Institutional HCI", r, 0, width=2)
    pat_cb = _field(scroll, "Patient *", r, 2, "combo", patients or ["No patients"])
    r += _field_row_advance(pan, pat_cb)
    ph_num = _field(scroll, "PhilHealth No. (PIN)", r, 0)
    d_adm  = _field(scroll, "Date Admitted (YYYY-MM-DD)", r, 1, default=str(date.today()))
    t_adm  = _field(scroll, "Time Admitted (HH:MM AM/PM)", r, 2)
    r += _field_row_advance(ph_num, d_adm, t_adm)
    d_dis  = _field(scroll, "Date Discharged (YYYY-MM-DD)", r, 0, default=str(date.today()))
    t_dis  = _field(scroll, "Time Discharged (HH:MM AM/PM)", r, 1)
    disp   = _field(scroll, "Disposition on Discharge", r, 2, "combo",
                    ["Improved", "Recovered", "HAMA", "Absconded",
                     "Expired", "Transferred"])
    r += _field_row_advance(d_dis, t_dis, disp)

    _section_hdr(scroll, "VITAL SIGNS & CHIEF COMPLAINT", r, span=3); r += 1
    chief  = _field(scroll, "Chief Complaint / Reason for Admission", r, 0, width=3); r += 2
    bp     = _field(scroll, "Blood Pressure", r, 0)
    pr     = _field(scroll, "Pulse Rate", r, 1)
    rr     = _field(scroll, "Respiratory Rate", r, 2)
    r += _field_row_advance(bp, pr, rr)
    temp   = _field(scroll, "Temperature (°C)", r, 0)
    wt     = _field(scroll, "Weight (kg)", r, 1)
    ht     = _field(scroll, "Height (cm)", r, 2)
    r += _field_row_advance(temp, wt, ht)

    _section_hdr(scroll, "PHYSICAL EXAMINATION – PERTINENT FINDINGS PER SYSTEM", r, span=3); r += 1
    genl   = _field(scroll, "General Survey", r, 0, "text", height=44)
    heent  = _field(scroll, "HEENT", r, 1, "text", height=44)
    chest  = _field(scroll, "Chest / Lungs", r, 2, "text", height=44)
    r += _field_row_advance(genl, heent, chest)
    cvs    = _field(scroll, "Cardiovascular (CVS)", r, 0, "text", height=44)
    abdom  = _field(scroll, "Abdomen", r, 1, "text", height=44)
    neuro  = _field(scroll, "Neurological", r, 2, "text", height=44)
    r += _field_row_advance(cvs, abdom, neuro)
    skin   = _field(scroll, "Skin / Extremities", r, 0, "text", height=44, width=3)
    r += _field_row_advance(skin)

    _section_hdr(scroll, "LABORATORY & DIAGNOSTIC FINDINGS", r, span=3); r += 1
    labs   = _field(scroll, "Pertinent Lab & Diagnostic Results (CBC, Urinalysis, X-ray, Biopsy, etc.)",
                    r, 0, "text", height=60, width=3)
    r += _field_row_advance(labs)

    _section_hdr(scroll, "COURSE IN THE WARDS", r, span=3); r += 1
    course = _field(scroll, "Course in the Wards (attach additional sheets if necessary)",
                    r, 0, "text", height=70, width=3)
    r += _field_row_advance(course)

    _section_hdr(scroll, "DIAGNOSIS & CASE RATE", r, span=3); r += 1
    dx     = _field(scroll, "Discharge Diagnosis", r, 0, width=2)
    icd    = _field(scroll, "ICD-10 Code", r, 2)
    r += _field_row_advance(dx, icd)
    cr     = _field(scroll, "Case Rate Code", r, 0)
    total  = _field(scroll, "Total Amount Claimed (₱)", r, 1, default="0")
    physn  = _field(scroll, "Attending Physician / Midwife", r, 2)
    r += _field_row_advance(cr, total, physn)
    prc    = _field(scroll, "PRC License No.", r, 0)
    ptr    = _field(scroll, "PTR No.", r, 1)
    phno   = _field(scroll, "Physician PhilHealth No.", r, 2)
    r += _field_row_advance(prc, ptr, phno)
    notes  = _field(scroll, "Notes / Remarks", r, 0, "text", height=44, width=3)
    r += _field_row_advance(notes)

    def _save():
        pid = _patient_id(pat_cb)
        _save_form(dlg, service, "CF3", {
            "patient_id":             pid,
            "philhealth_number":      _get(ph_num),
            "diagnosis":              _get(dx),
            "icd_code":               _get(icd),
            "case_rate_code":         _get(cr),
            "total_amount_claimed":   _get(total) or "0",
            "admission_date":         _parse_date(_get(d_adm)),
            "discharge_date":         _parse_date(_get(d_dis)),
            "time_admitted":          _get(t_adm),
            "time_discharged":        _get(t_dis),
            "patient_disposition":    _get(disp),
            "physician_name":         _get(physn),
            "physician_prc_no":       _get(prc),
            "physician_ptr_no":       _get(ptr),
            "physician_philhealth_no":_get(phno),
            "type_of_claim":          "Clinical Record",
            "professional_fee_claimed": 0,
            "professional_fee_share": 0,
            "notes": (
                f"PAN:{_get(pan)} BP:{_get(bp)} PR:{_get(pr)} RR:{_get(rr)} "
                f"TEMP:{_get(temp)} WT:{_get(wt)} HT:{_get(ht)} "
                f"CHIEF:{_get(chief)} GENL:{_get(genl)} HEENT:{_get(heent)} "
                f"CHEST:{_get(chest)} CVS:{_get(cvs)} ABD:{_get(abdom)} "
                f"NEURO:{_get(neuro)} SKIN:{_get(skin)} "
                f"LABS:{_get(labs)} COURSE:{_get(course)} {_get(notes)}"
            ),
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  CF4 – All Case Rates / Outpatient
# ─────────────────────────────────────────────────────────────────────────────

def _CF4Dialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CF4 – All Case Rates (Outpatient/ER)", w=920, h=780)
    _dialog_banner(dlg, "CF4 – All Case Rates / Outpatient Claim Form",
                   "Philippine Health Insurance Corporation  |  February 2020")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white", corner_radius=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)
    r = 0

    # ── Part I: HCI ─────────────────────────────────────────────────────────
    _section_hdr(scroll, "PART I – HEALTH CARE INSTITUTION (HCI) INFORMATION", r, span=4); r += 1
    hci_n  = _field(scroll, "Name of HCI", r, 0, width=2)
    hci_an = _field(scroll, "Accreditation No.", r, 2)
    hci_a  = _field(scroll, "Address of HCI", r, 3)
    r += _field_row_advance(hci_n, hci_an, hci_a)

    # ── Part II: Patient Data ────────────────────────────────────────────────
    _section_hdr(scroll, "PART II – PATIENT'S DATA", r, span=4); r += 1
    pat_cb = _field(scroll, "Patient *", r, 0, "combo", patients or ["No patients"], width=2)
    ph_num = _field(scroll, "PhilHealth No. (PIN)", r, 2)
    age    = _field(scroll, "Age", r, 3)
    r += _field_row_advance(pat_cb, ph_num, age)
    sex_cb = _field(scroll, "Sex", r, 0, "combo", ["Male", "Female"])
    chief  = _field(scroll, "Chief Complaint", r, 1, width=3)
    r += _field_row_advance(sex_cb, chief)
    adm_dx = _field(scroll, "Admitting Diagnosis", r, 0, width=2)
    dis_dx = _field(scroll, "Discharge Diagnosis", r, 2, width=2)
    r += _field_row_advance(adm_dx, dis_dx)
    icd    = _field(scroll, "ICD-10 Code", r, 0)
    cr1    = _field(scroll, "1st Case Rate Code", r, 1)
    cr2    = _field(scroll, "2nd Case Rate Code", r, 2)
    rvs    = _field(scroll, "RVS Code (Surgical Procedure)", r, 3)
    r += _field_row_advance(icd, cr1, cr2, rvs)
    d_adm  = _field(scroll, "Date Admitted (YYYY-MM-DD)", r, 0, default=str(date.today()))
    t_adm  = _field(scroll, "Time Admitted", r, 1)
    d_dis  = _field(scroll, "Date Discharged (YYYY-MM-DD)", r, 2, default=str(date.today()))
    t_dis  = _field(scroll, "Time Discharged", r, 3)
    r += _field_row_advance(d_adm, t_adm, d_dis, t_dis)

    # ── Part III: Reason for Admission ──────────────────────────────────────
    _section_hdr(scroll, "PART III – REASON FOR ADMISSION", r, span=4); r += 1
    hist   = _field(scroll, "History of Present Illness", r, 0, "text",
                    height=60, width=4)
    r += _field_row_advance(hist)
    pmh    = _field(scroll, "Pertinent Past Medical History", r, 0, "text",
                    height=44, width=2)
    ob     = _field(scroll, "OB/GYN History (if applicable)", r, 2, "text",
                    height=44, width=2)
    r += _field_row_advance(pmh, ob)
    phys   = _field(scroll, "Physical Examination Findings", r, 0, "text",
                    height=60, width=4)
    r += _field_row_advance(phys)

    # ── Part IV+V: Course + Drugs ────────────────────────────────────────────
    _section_hdr(scroll, "PART IV – COURSE IN THE WARD / SURGICAL PROCEDURES", r, span=4); r += 1
    course = _field(scroll, "Doctor's Orders / Surgical Procedures (attach OR technique)",
                    r, 0, "text", height=60, width=4)
    r += _field_row_advance(course)
    _section_hdr(scroll, "PART V – DRUGS / MEDICINES", r, span=4); r += 1
    drugs  = _field(scroll, "Drugs / Medicines (Generic Name, Dosage, Frequency)",
                    r, 0, "text", height=44, width=4)
    r += _field_row_advance(drugs)

    # ── Part VI+VII: Outcome + Charges ──────────────────────────────────────
    _section_hdr(scroll, "PART VI – OUTCOME  &  CHARGES", r, span=4); r += 1
    outc   = _field(scroll, "Outcome of Treatment", r, 0, "combo",
                    ["Improved", "Recovered", "HAMA", "Expired",
                     "Absconded", "Transferred"])
    physn  = _field(scroll, "Attending Physician", r, 1)
    prc    = _field(scroll, "PRC License No.", r, 2)
    phno   = _field(scroll, "Physician PhilHealth No.", r, 3)
    r += _field_row_advance(outc, physn, prc, phno)

    total  = _field(scroll, "Total Amount Claimed (₱)", r, 0, default="0")
    conslt = _field(scroll, "Consultation / PF Charges (₱)", r, 1, default="0")
    meds   = _field(scroll, "Medicine / Supplies (₱)", r, 2, default="0")
    labx   = _field(scroll, "Lab / Diagnostics (₱)", r, 3, default="0")
    r += _field_row_advance(total, conslt, meds, labx)
    oth    = _field(scroll, "Other Charges (₱)", r, 0, default="0")
    hsp    = _field(scroll, "PhilHealth Benefit / Hospital Share (₱)", r, 1, default="0")
    notes  = _field(scroll, "Notes / Remarks", r, 2, "text", height=44, width=2)
    r += _field_row_advance(oth, hsp, notes)

    def _save():
        pid = _patient_id(pat_cb)
        _save_form(dlg, service, "CF4", {
            "patient_id":             pid,
            "philhealth_number":      _get(ph_num),
            "diagnosis":              _get(dis_dx) or _get(adm_dx),
            "icd_code":               _get(icd),
            "case_rate_code":         _get(cr1),
            "second_case_rate_code":  _get(cr2),
            "total_amount_claimed":   _get(total) or "0",
            "admission_date":         _parse_date(_get(d_adm)),
            "discharge_date":         _parse_date(_get(d_dis)),
            "time_admitted":          _get(t_adm),
            "time_discharged":        _get(t_dis),
            "patient_disposition":    _get(outc),
            "admission_diagnosis":    _get(adm_dx),
            "attending_physician":    _get(physn),
            "room_charges":           _get(conslt) or "0",
            "medicine_charges":       _get(meds) or "0",
            "xray_lab_charges":       _get(labx) or "0",
            "other_charges":          _get(oth) or "0",
            "hospital_share":         _get(hsp) or "0",
            "notes": (
                f"HCI:{_get(hci_n)} AN:{_get(hci_an)} ADDR:{_get(hci_a)} "
                f"AGE:{_get(age)} SEX:{_get(sex_cb)} CHIEF:{_get(chief)} "
                f"RVS:{_get(rvs)} CR2:{_get(cr2)} "
                f"HIST:{_get(hist)} PMH:{_get(pmh)} OB:{_get(ob)} "
                f"PHYS:{_get(phys)} COURSE:{_get(course)} "
                f"DRUGS:{_get(drugs)} PRC:{_get(prc)} PHNO:{_get(phno)} {_get(notes)}"
            ),
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  CF5 – ESRD / Dialysis
# ─────────────────────────────────────────────────────────────────────────────

def _CF5Dialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CF5 – ESRD / Dialysis Claim", w=820, h=580)
    _dialog_banner(dlg, "CF5 – ESRD / Dialysis Claim",
                   "Philippine Health Insurance Corporation")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white", corner_radius=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2), weight=1)
    r = 0

    _section_hdr(scroll, "PATIENT & DIALYSIS INFORMATION", r, span=3); r += 1
    pat_cb = _field(scroll, "Patient *", r, 0, "combo", patients or ["No patients"], width=2)
    ph_num = _field(scroll, "PhilHealth No. (PIN)", r, 2)
    r += _field_row_advance(pat_cb, ph_num)
    dx     = _field(scroll, "Diagnosis", r, 0, width=2)
    icd    = _field(scroll, "ICD-10 Code", r, 2)
    r += _field_row_advance(dx, icd)
    cr     = _field(scroll, "Case Rate Code", r, 0)
    total  = _field(scroll, "Total Amount Claimed (₱)", r, 1, default="0")
    r += _field_row_advance(cr, total)

    _section_hdr(scroll, "DIALYSIS DETAILS", r, span=3); r += 1
    cname  = _field(scroll, "Dialysis Center Name", r, 0, width=2)
    cacc   = _field(scroll, "Center Accreditation No.", r, 2)
    r += _field_row_advance(cname, cacc)
    dtype  = _field(scroll, "Dialysis Type", r, 0, "combo",
                    ["Hemodialysis", "Peritoneal Dialysis"])
    sess   = _field(scroll, "Number of Sessions", r, 1, default="0")
    pfrom  = _field(scroll, "Period From (YYYY-MM-DD)", r, 2,
                    default=str(date.today()))
    r += _field_row_advance(dtype, sess, pfrom)
    pto    = _field(scroll, "Period To (YYYY-MM-DD)", r, 0, default=str(date.today()))
    notes  = _field(scroll, "Notes / Remarks", r, 1, width=2)
    r += _field_row_advance(pto, notes)

    def _save():
        pid = _patient_id(pat_cb)
        _save_form(dlg, service, "CF5", {
            "patient_id":                    pid,
            "philhealth_number":             _get(ph_num),
            "diagnosis":                     _get(dx),
            "icd_code":                      _get(icd),
            "case_rate_code":                _get(cr),
            "total_amount_claimed":          _get(total) or "0",
            "dialysis_center_name":          _get(cname),
            "dialysis_center_accreditation": _get(cacc),
            "dialysis_type":                 _get(dtype),
            "number_of_sessions":            int(_get(sess) or 0),
            "period_from":                   _parse_date(_get(pfrom)),
            "period_to":                     _parse_date(_get(pto)),
            "notes":                         _get(notes),
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  CSF – Claim Signature Form
# ─────────────────────────────────────────────────────────────────────────────

def _CSFDialog(master, patients: list, service, on_saved) -> None:
    dlg = _make_dialog(master, "CSF – Claim Signature Form", w=840, h=660)
    _dialog_banner(dlg, "CSF – Claim Signature Form",
                   "Republic of the Philippines  |  Philippine Health Insurance Corporation  |  Revised September 2018")

    scroll = ctk.CTkScrollableFrame(dlg, fg_color="white", corner_radius=0)
    scroll.grid(row=1, column=0, sticky="nsew")
    scroll.grid_columnconfigure((0, 1, 2), weight=1)
    r = 0

    # ── Part I: Member / Patient ─────────────────────────────────────────────
    _section_hdr(scroll, "PART I – MEMBER AND PATIENT INFORMATION AND CERTIFICATION", r, span=3); r += 1
    pat_cb = _field(scroll, "Patient / Member *", r, 0, "combo",
                    patients or ["No patients"], width=2)
    ph_num = _field(scroll, "PhilHealth Identification No. (PIN)", r, 2)
    r += _field_row_advance(pat_cb, ph_num)
    dob    = _field(scroll, "Member Date of Birth (YYYY-MM-DD)", r, 0)
    dep_rel= _field(scroll, "Patient Relationship to Member", r, 1, "combo",
                    ["Member (Same Person)", "Child", "Parent", "Spouse"])
    dep_pin= _field(scroll, "PhilHealth PIN of Dependent (if applicable)", r, 2)
    r += _field_row_advance(dob, dep_rel, dep_pin)

    d_adm  = _field(scroll, "Date Admitted (YYYY-MM-DD)", r, 0, default=str(date.today()))
    d_dis  = _field(scroll, "Date Discharged (YYYY-MM-DD)", r, 1, default=str(date.today()))
    dx     = _field(scroll, "Diagnosis / ICD Code", r, 2)
    r += _field_row_advance(d_adm, d_dis, dx)
    cr1    = _field(scroll, "1st Case Rate Code", r, 0)
    cr2    = _field(scroll, "2nd Case Rate Code (if any)", r, 1)
    total  = _field(scroll, "Total Amount Claimed (₱)", r, 2, default="0")
    r += _field_row_advance(cr1, cr2, total)

    # ── Part II: Employer ────────────────────────────────────────────────────
    _section_hdr(scroll, "PART II – EMPLOYER'S CERTIFICATION (employed members only)", r, span=3); r += 1
    pen    = _field(scroll, "PhilHealth Employer No. (PEN)", r, 0)
    emp_tel= _field(scroll, "Contact No.", r, 1)
    emp_nm = _field(scroll, "Business Name of Employer", r, 2)
    r += _field_row_advance(pen, emp_tel, emp_nm)

    # ── Part IV: HCP Accreditations ──────────────────────────────────────────
    _section_hdr(scroll, "PART IV – HEALTH CARE PROFESSIONAL INFORMATION", r, span=3); r += 1
    hcp1   = _field(scroll, "HCP 1 – Accreditation No.", r, 0)
    hcp2   = _field(scroll, "HCP 2 – Accreditation No.", r, 1)
    hcp3   = _field(scroll, "HCP 3 – Accreditation No.", r, 2)
    r += _field_row_advance(hcp1, hcp2, hcp3)

    # ── Part V: Provider ─────────────────────────────────────────────────────
    _section_hdr(scroll, "PART V – PROVIDER INFORMATION AND CERTIFICATION", r, span=3); r += 1
    pan    = _field(scroll, "PhilHealth Accreditation No. (PAN) of HCI", r, 0)
    hci_n  = _field(scroll, "Name of HCI", r, 1, width=2)
    r += _field_row_advance(pan, hci_n)
    notes  = _field(scroll, "Notes / Remarks", r, 0, "text", height=44, width=3)
    r += _field_row_advance(notes)

    def _save():
        pid = _patient_id(pat_cb)
        _save_form(dlg, service, "CSF", {
            "patient_id":             pid,
            "philhealth_number":      _get(ph_num),
            "diagnosis":              _get(dx),
            "icd_code":               "",
            "case_rate_code":         _get(cr1),
            "second_case_rate_code":  _get(cr2),
            "total_amount_claimed":   _get(total) or "0",
            "admission_date":         _parse_date(_get(d_adm)),
            "discharge_date":         _parse_date(_get(d_dis)),
            "notes": (
                f"DOB:{_get(dob)} REL:{_get(dep_rel)} DEP_PIN:{_get(dep_pin)} "
                f"PEN:{_get(pen)} EMPTEL:{_get(emp_tel)} EMPNM:{_get(emp_nm)} "
                f"HCP1:{_get(hcp1)} HCP2:{_get(hcp2)} HCP3:{_get(hcp3)} "
                f"PAN:{_get(pan)} HCI:{_get(hci_n)} {_get(notes)}"
            ),
            "date_of_claim": date.today(),
        }, on_saved)

    _dialog_footer(dlg, _save)


# ─────────────────────────────────────────────────────────────────────────────
#  View Claim Form Details Dialog
# ─────────────────────────────────────────────────────────────────────────────

class _ViewClaimDialog(ctk.CTkToplevel):
    """Read-only full details of a PhilHealth claim form with member info."""

    def __init__(self, master, form, **kwargs):
        super().__init__(master, **kwargs)
        ft_labels = {
            "CF2": "CF2 – Hospital / Facility Claim",
            "CF3": "CF3 – Professional Fee Claim",
            "CF4": "CF4 – All Case Rates / Outpatient",
            "CF5": "CF5 – ESRD / Dialysis Claim",
        }
        self.title(f"Claim Form Details  —  {form.form_number}")
        self.geometry("760x640")
        self.resizable(True, True)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Banner ──────────────────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=Theme.ACCENT, corner_radius=0, height=64)
        banner.grid(row=0, column=0, sticky="ew")
        banner.grid_propagate(False)
        banner.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(banner, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=20, pady=12)
        ctk.CTkLabel(
            left, text=ft_labels.get(form.form_type, form.form_type),
            font=Theme.FONT_HEADING, text_color="white", anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text=f"Form No: {form.form_number}",
            font=Theme.FONT_TINY, text_color="#BFDBFE", anchor="w",
        ).pack(anchor="w")

        status_color = _STATUS_COLORS.get(form.status, Theme.TEXT_MUTED)
        ctk.CTkLabel(
            banner, text=f"● {form.status}",
            font=("Segoe UI", 12, "bold"), text_color=status_color, anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=20)

        # ── Scrollable body ─────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=Theme.PAGE_BG)
        body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        body.grid_columnconfigure(0, weight=1)

        patient = form.patient

        # ── PhilHealth Member Info ───────────────────────────────────────────
        self._section(body, "PhilHealth Member Information", row=0)
        mem_card = self._card(body, row=1)
        mem_card.grid_columnconfigure((0, 1, 2), weight=1)

        ph_num   = form.philhealth_number or (patient.philhealth_number if patient else "—") or "—"
        mem_type = (patient.philhealth_member_type if patient else None) or "—"
        category = (patient.philhealth_category if patient else None) or "—"

        for col, (lbl, val) in enumerate([
            ("Full Name",            patient.full_name if patient else "—"),
            ("PhilHealth No.",       ph_num),
            ("Member Type",          mem_type),
        ]):
            self._field(mem_card, lbl, val, row=0, col=col)

        for col, (lbl, val) in enumerate([
            ("Date of Birth",        str(patient.birth_date or "—") if patient else "—"),
            ("Gender",               (patient.gender or "—") if patient else "—"),
            ("Contact No.",          (patient.contact_number or "—") if patient else "—"),
        ]):
            self._field(mem_card, lbl, val, row=1, col=col)

        for col, (lbl, val) in enumerate([
            ("PhilHealth Category",  category),
            ("Senior Citizen",       ("Yes" if patient and patient.is_senior_citizen else "No") if patient else "—"),
            ("PWD",                  ("Yes" if patient and patient.is_pwd else "No") if patient else "—"),
        ]):
            self._field(mem_card, lbl, val, row=2, col=col)

        # ── Claim Form Details ───────────────────────────────────────────────
        self._section(body, "Claim Form Details", row=2)
        cf_card = self._card(body, row=3)
        cf_card.grid_columnconfigure((0, 1, 2), weight=1)

        self._field(cf_card, "Form Number",      form.form_number,                              row=0, col=0)
        self._field(cf_card, "Form Type",        ft_labels.get(form.form_type, form.form_type), row=0, col=1)
        self._field(cf_card, "Status",           form.status,                                   row=0, col=2)
        self._field(cf_card, "Date of Claim",    str(form.date_of_claim or "—"),                row=1, col=0)
        self._field(cf_card, "Diagnosis",        form.diagnosis or "—",                         row=1, col=1)
        self._field(cf_card, "ICD-10 Code",      form.icd_code or "—",                         row=1, col=2)
        self._field(cf_card, "Case Rate Code",   form.case_rate_code or "—",                    row=2, col=0)
        self._field(cf_card, "Total Claimed",    format_currency(form.total_amount_claimed),    row=2, col=1)
        self._field(cf_card, "Notes",            form.notes or "—",                             row=2, col=2)

        # ── Form-type specific fields ────────────────────────────────────────
        if form.form_type == "CF2":
            self._section(body, "CF2 – Hospital / Facility Details", row=4)
            sp = self._card(body, row=5)
            sp.grid_columnconfigure((0, 1, 2), weight=1)
            self._field(sp, "Admission Date",         str(form.admission_date or "—"),   row=0, col=0)
            self._field(sp, "Discharge Date",         str(form.discharge_date or "—"),   row=0, col=1)
            self._field(sp, "Type of Admission",      form.type_of_admission or "—",     row=0, col=2)
            self._field(sp, "Room & Board Charges",   format_currency(form.room_charges),     row=1, col=0)
            self._field(sp, "Medicine Charges",       format_currency(form.medicine_charges), row=1, col=1)
            self._field(sp, "X-Ray / Lab Charges",    format_currency(form.xray_lab_charges), row=1, col=2)
            self._field(sp, "Other Charges",          format_currency(form.other_charges),    row=2, col=0)
            self._field(sp, "Hospital Share (PhilHealth)", format_currency(form.hospital_share), row=2, col=1)

        elif form.form_type == "CF3":
            self._section(body, "CF3 – Professional Fee Details", row=4)
            sp = self._card(body, row=5)
            sp.grid_columnconfigure((0, 1, 2), weight=1)
            self._field(sp, "Physician Name",          form.physician_name or "—",               row=0, col=0)
            self._field(sp, "PRC License No.",         form.physician_prc_no or "—",             row=0, col=1)
            self._field(sp, "PTR No.",                 form.physician_ptr_no or "—",             row=0, col=2)
            self._field(sp, "Physician PhilHealth No.",form.physician_philhealth_no or "—",      row=1, col=0)
            self._field(sp, "Type of Claim",           form.type_of_claim or "—",                row=1, col=1)
            self._field(sp, "Prof. Fee Claimed",       format_currency(form.professional_fee_claimed), row=1, col=2)
            self._field(sp, "Prof. Fee – PhilHealth Share", format_currency(form.professional_fee_share), row=2, col=0)

        elif form.form_type == "CF4":
            self._section(body, "CF4 – All Case Rates / Outpatient Details", row=4)
            sp = self._card(body, row=5)
            sp.grid_columnconfigure((0, 1, 2), weight=1)
            self._field(sp, "Consultation Charges",   format_currency(form.room_charges),        row=0, col=0)
            self._field(sp, "Medicine / Supplies",    format_currency(form.medicine_charges),    row=0, col=1)
            self._field(sp, "Lab / Diagnostics",      format_currency(form.xray_lab_charges),    row=0, col=2)
            self._field(sp, "Other Charges",          format_currency(form.other_charges),       row=1, col=0)
            self._field(sp, "PhilHealth Benefit",     format_currency(form.hospital_share),      row=1, col=1)

        elif form.form_type == "CF5":
            self._section(body, "CF5 – ESRD / Dialysis Details", row=4)
            sp = self._card(body, row=5)
            sp.grid_columnconfigure((0, 1, 2), weight=1)
            self._field(sp, "Dialysis Center",        form.dialysis_center_name or "—",          row=0, col=0)
            self._field(sp, "Accreditation No.",      form.dialysis_center_accreditation or "—", row=0, col=1)
            self._field(sp, "Dialysis Type",          form.dialysis_type or "—",                 row=0, col=2)
            self._field(sp, "Period From",            str(form.period_from or "—"),              row=1, col=0)
            self._field(sp, "Period To",              str(form.period_to or "—"),                row=1, col=1)
            self._field(sp, "No. of Sessions",        str(form.number_of_sessions or "—"),       row=1, col=2)

        # ── eClaims Status ───────────────────────────────────────────────────
        if getattr(form, "eclaim_status", None) and form.eclaim_status != "Pending":
            self._section(body, "eClaims Transmission", row=6)
            ec = self._card(body, row=7)
            ec.grid_columnconfigure((0, 1, 2), weight=1)
            self._field(ec, "eClaim Status",   form.eclaim_status or "—",                           row=0, col=0)
            self._field(ec, "Reference No.",   getattr(form, "eclaim_ref_no", None) or "—",         row=0, col=1)
            submitted = str(getattr(form, "eclaim_submitted_at", None) or "")[:16] or "—"
            self._field(ec, "Transmitted At",  submitted,                                           row=0, col=2)
            notes_val = getattr(form, "eclaim_notes", None) or "—"
            self._field(ec, "Transmission Notes", notes_val,                                        row=1, col=0)

        # ── Footer ──────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=Theme.PRIMARY, height=56, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            footer, text="Close", width=100, height=36,
            font=Theme.FONT_BUTTON, fg_color=Theme.SECONDARY,
            text_color=Theme.TEXT_PRIMARY, hover_color=Theme.BORDER,
            border_width=1, border_color=Theme.BORDER,
            corner_radius=Theme.BUTTON_RADIUS,
            command=self.destroy,
        ).grid(row=0, column=0, pady=10, padx=20, sticky="e")

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _section(self, parent, title: str, row: int) -> None:
        ctk.CTkLabel(
            parent, text=title, font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(16, 4))

    def _card(self, parent, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 4))
        return card

    def _field(self, parent, label: str, value: str, row: int, col: int) -> None:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, sticky="w", padx=16, pady=10)
        ctk.CTkLabel(
            f, text=label, font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            f, text=str(value), font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY, anchor="w", wraplength=200,
        ).pack(anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
#  eClaims Transmission Dialog
# ─────────────────────────────────────────────────────────────────────────────

class _EClaimTransmitDialog(ctk.CTkToplevel):
    """Attach supporting PDFs, auto-generate the claim form PDF, and transmit."""

    def __init__(self, master, form, philhealth_service, clinic_info: dict,
                 on_transmitted, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"Transmit eClaim  —  {form.form_number}")
        self.geometry("860x640")
        self.resizable(True, True)
        self.grab_set()

        self.form = form
        self.service = philhealth_service
        self.clinic_info = clinic_info
        self.on_transmitted = on_transmitted
        self._docs: list[dict] = normalize_supporting_docs(
            json.loads(form.supporting_docs or "[]"),
            default_form_type=form.form_type,
        )
        self._zip_path: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

        if form.eclaim_status == "Transmitted":
            self._show_result(
                f"Previously transmitted  —  Ref: {form.eclaim_ref_no}\n"
                f"Submitted: {str(form.eclaim_submitted_at or '')[:16]}",
                is_error=False,
            )

    # ── layout ──────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Header banner
        hdr = ctk.CTkFrame(self, fg_color=Theme.ACCENT_LIGHT, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        patient_name = self.form.patient.full_name if self.form.patient else "—"
        ctk.CTkLabel(hdr, text="eClaim Online Transmission",
                     font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY
                     ).pack(anchor="w", padx=20, pady=(14, 2))
        ctk.CTkLabel(hdr,
                     text=f"{self.form.form_number}  ·  {self.form.form_type}  ·  {patient_name}",
                     font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY
                     ).pack(anchor="w", padx=20, pady=(0, 14))

        # Scrollable body
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        body.grid_columnconfigure(0, weight=1)

        # ── Claim summary card ──────────────────────────────────────────────
        card = ctk.CTkFrame(body, fg_color=Theme.CARD_BG,
                            corner_radius=Theme.CORNER_RADIUS,
                            border_width=1, border_color=Theme.BORDER)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure((0, 1, 2), weight=1)

        for (lbl, val, r, c) in [
            ("PhilHealth No.",  self.form.philhealth_number,                  0, 0),
            ("Diagnosis",       (self.form.diagnosis or "—")[:38],            0, 1),
            ("ICD-10 Code",     self.form.icd_code,                           0, 2),
            ("Case Rate Code",  self.form.case_rate_code,                     1, 0),
            ("Total Claimed",   f"₱{float(self.form.total_amount_claimed):,.2f}", 1, 1),
            ("Date of Claim",   str(self.form.date_of_claim or "—"),          1, 2),
        ]:
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.grid(row=r, column=c, sticky="w", padx=16, pady=10)
            ctk.CTkLabel(f, text=lbl, font=Theme.FONT_TINY,
                         text_color=Theme.TEXT_SECONDARY).pack(anchor="w")
            ctk.CTkLabel(f, text=val or "—", font=Theme.FONT_BODY,
                         text_color=Theme.TEXT_PRIMARY).pack(anchor="w")

        # ── Supporting documents ────────────────────────────────────────────
        docs_hdr = ctk.CTkFrame(body, fg_color="transparent")
        docs_hdr.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(docs_hdr, text="Supporting Documents (SOA XML + PDFs)",
                     font=Theme.FONT_SUBHEADING,
                     text_color=Theme.TEXT_PRIMARY).pack(side="left")
        ActionButton(docs_hdr, text="Auto-Generate Claim PDF", style="secondary",
                     command=self._auto_generate_pdf).pack(side="right", padx=(6, 0))
        ActionButton(docs_hdr, text="+ Attach PDF/XML", style="secondary",
                     command=self._add_docs).pack(side="right")

        ctk.CTkLabel(
            body,
            text="SOA XML attached from Billing appears here automatically. "
                 "Set the document type (CF2, CF3, SOA XML, etc.) for each file before transmitting.",
            font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
            wraplength=780,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self._docs_frame = ctk.CTkFrame(body, fg_color=Theme.CARD_BG,
                                        corner_radius=Theme.CORNER_RADIUS,
                                        border_width=1, border_color=Theme.BORDER)
        self._docs_frame.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self._docs_frame.grid_columnconfigure(0, weight=1)
        self._refresh_docs()

        # ── Notes ───────────────────────────────────────────────────────────
        ctk.CTkLabel(body, text="Transmission Notes", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_SECONDARY, anchor="w"
                     ).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.notes_box = ctk.CTkTextbox(body, height=56, font=Theme.FONT_BODY)
        self.notes_box.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        if self.form.eclaim_notes:
            self.notes_box.insert("1.0", self.form.eclaim_notes)

        # ── Result message ──────────────────────────────────────────────────
        self.result_lbl = ctk.CTkLabel(body, text="", font=Theme.FONT_SMALL,
                                       text_color=Theme.SUCCESS, anchor="w",
                                       justify="left", wraplength=700)
        self.result_lbl.grid(row=6, column=0, sticky="ew")

        # ── Footer ──────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        self.transmit_btn = ActionButton(
            footer, text="⊕  Generate Package & Transmit",
            style="success", command=self._transmit
        )
        self.transmit_btn.pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Close", style="secondary",
                     command=self.destroy).pack(side="left")
        self.open_folder_btn = ActionButton(footer, text="Open Package Folder",
                                             style="secondary",
                                             command=self._open_folder)

    # ── docs list ────────────────────────────────────────────────────────────
    def _persist_docs(self) -> None:
        self.service.update_supporting_docs(self.form.id, self._docs)

    def _refresh_docs(self) -> None:
        for w in self._docs_frame.winfo_children():
            w.destroy()

        if not self._docs:
            ctk.CTkLabel(
                self._docs_frame,
                text="No documents yet. Attach SOA XML from Billing, "
                     "or add PDF/XML files here.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=14, padx=16)
            return

        hdr = ctk.CTkFrame(self._docs_frame, fg_color=Theme.SECONDARY, height=32)
        hdr.pack(fill="x", padx=8, pady=(8, 4))
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="Document", font=Theme.FONT_TINY,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left", padx=(12, 0))
        ctk.CTkLabel(
            hdr, text="Document Type", font=Theme.FONT_TINY,
            text_color=Theme.TEXT_SECONDARY, anchor="e",
        ).pack(side="right", padx=(0, 100))

        for entry in self._docs:
            path = entry["path"]
            p = Path(path)
            exists = p.exists()
            is_xml = p.suffix.lower() == ".xml"
            row = ctk.CTkFrame(self._docs_frame, fg_color="transparent", height=40)
            row.pack(fill="x", padx=12, pady=2)
            row.pack_propagate(False)

            color = Theme.TEXT_PRIMARY if exists else Theme.DANGER
            kind = "XML" if is_xml else "PDF"
            icon = "◈" if exists else "✕"
            ctk.CTkLabel(
                row, text=f"  {icon}  [{kind}]  {p.name}",
                font=Theme.FONT_SMALL, text_color=color, anchor="w",
            ).pack(side="left", fill="both", expand=True)

            type_combo = ctk.CTkComboBox(
                row,
                values=ECLAIM_DOCUMENT_TYPES,
                width=200,
                height=28,
                font=Theme.FONT_TINY,
                dropdown_font=Theme.FONT_TINY,
                corner_radius=Theme.BUTTON_RADIUS,
                border_color=Theme.BORDER,
                button_color=Theme.ACCENT,
                button_hover_color=Theme.ACCENT_HOVER,
                command=lambda v, pt=path: self._set_doc_type(pt, v),
            )
            type_combo.set(entry.get("doc_type") or "Other")
            type_combo.pack(side="right", padx=(8, 4))

            ctk.CTkButton(
                row, text="Remove", width=64, height=24,
                font=Theme.FONT_TINY, fg_color="transparent",
                text_color=Theme.DANGER, hover_color=Theme.DANGER_LIGHT,
                command=lambda pt=path: self._remove_doc(pt),
            ).pack(side="right", padx=4)

    def _set_doc_type(self, path: str, doc_type: str) -> None:
        for entry in self._docs:
            if entry["path"] == path:
                entry["doc_type"] = doc_type
                break
        self._persist_docs()

    def _add_docs(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self, title="Select Supporting Documents",
            filetypes=[
                ("PDF and XML", "*.pdf;*.xml"),
                ("PDF Files", "*.pdf"),
                ("XML Files", "*.xml"),
                ("All Files", "*.*"),
            ],
        )
        existing = {d["path"] for d in self._docs}
        for p in paths:
            if p not in existing:
                self._docs.append({
                    "path": p,
                    "doc_type": guess_eclaim_document_type(p, self.form.form_type),
                })
                existing.add(p)
        self._refresh_docs()
        self._persist_docs()

    def _remove_doc(self, path: str) -> None:
        self._docs = [d for d in self._docs if d["path"] != path]
        self._refresh_docs()
        self._persist_docs()

    def _auto_generate_pdf(self) -> None:
        """Generate the claim form PDF and prepend it to the docs list."""
        out_dir = Path(ECLAIMS_DIR) / self.form.form_number
        out_dir.mkdir(parents=True, exist_ok=True)

        patient     = self.form.patient
        clinic      = self.clinic_info.get("clinic_name", "Clinic")
        addr        = self.clinic_info.get("clinic_address", "")
        accred      = self.clinic_info.get("accreditation", "")
        pname       = patient.full_name if patient else "—"
        ph_num      = self.form.philhealth_number or "—"
        mem_type    = (patient.philhealth_member_type if patient else None) or "—"
        safe_name   = "".join(c for c in pname if c not in '\\/:*?"<>|') or "Patient"
        pdf_path    = str(out_dir / f"{safe_name} - {self.form.form_type}.pdf")

        try:
            # Use the same central helper used by Print PDF button
            _view = self.master
            while _view and not hasattr(_view, "_generate_form_pdf"):
                _view = getattr(_view, "master", None)
            if _view:
                _view._generate_form_pdf(self.form, pdf_path, clinic, addr, accred)
            else:
                PDFGenerator.generate_cf2_cf4(
                    output_path=pdf_path, clinic_name=clinic, clinic_address=addr,
                    accreditation_no=accred, form_number=self.form.form_number,
                    patient_name=pname, philhealth_number=ph_num,
                    member_type=mem_type, form_type=self.form.form_type,
                    diagnosis=self.form.diagnosis or "—",
                    icd_code=self.form.icd_code or "—",
                    case_rate_code=self.form.case_rate_code or "—",
                    second_case_rate_code="—",
                    total_claimed=float(self.form.total_amount_claimed or 0),
                    date_of_claim=str(self.form.date_of_claim or date.today()),
                    admission_date=str(self.form.admission_date or "—"),
                    discharge_date=str(self.form.discharge_date or "—"),
                    time_admitted="—", time_discharged="—",
                    type_of_admission=self.form.type_of_admission or "—",
                    patient_disposition="—", accommodation_type="—",
                    admission_diagnosis=self.form.diagnosis or "—",
                    referring_hci="—", attending_physician="—",
                    room_charges=float(self.form.room_charges or 0),
                    medicine_charges=float(self.form.medicine_charges or 0),
                    xray_lab_charges=float(self.form.xray_lab_charges or 0),
                    other_charges=float(self.form.other_charges or 0),
                    hospital_share=float(self.form.hospital_share or 0),
                    notes=self.form.notes or "",
                )

            if not any(d["path"] == pdf_path for d in self._docs):
                self._docs.insert(0, {
                    "path": pdf_path,
                    "doc_type": self.form.form_type or guess_eclaim_document_type(
                        pdf_path, self.form.form_type
                    ),
                })
            self._refresh_docs()
            self._persist_docs()
            show_message(self, "PDF Generated",
                         f"Claim form PDF saved:\n{pdf_path}", "success")
        except Exception as exc:
            show_message(self, "PDF Error", str(exc), "error")

    # ── transmit ─────────────────────────────────────────────────────────────
    def _transmit(self) -> None:
        notes = self.notes_box.get("1.0", "end").strip()
        ok, msg, zip_path = self.service.transmit_eclaim(
            self.form.id, self._docs, notes
        )
        if ok:
            self._zip_path = zip_path
            self.form = self.service.claim_form_repo.get_by_id(self.form.id)
            ref = self.form.eclaim_ref_no if self.form else "—"
            self._show_result(
                f"✓  Transmitted successfully!\n"
                f"   Reference No.: {ref}\n"
                f"   Package: {zip_path}",
                is_error=False,
            )
            self.open_folder_btn.pack(side="left", padx=(8, 0))
            self.transmit_btn.configure(text="Re-Transmit")
            self.on_transmitted()
        else:
            self._show_result(f"✗  {msg}", is_error=True)

    def _show_result(self, text: str, is_error: bool = False) -> None:
        self.result_lbl.configure(
            text=text,
            text_color=Theme.DANGER if is_error else Theme.SUCCESS,
        )

    def _open_folder(self) -> None:
        if self._zip_path:
            os.startfile(str(Path(self._zip_path).parent))


# ─────────────────────────────────────────────────────────────────────────────
#  Main PhilHealth view
# ─────────────────────────────────────────────────────────────────────────────

class PhilHealthView(ctk.CTkFrame):
    def __init__(self, master, philhealth_service, patient_service,
                 settings_service=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = philhealth_service
        self.patient_service = patient_service
        self.settings_service = settings_service
        self.computation = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "PhilHealth",
                   "Benefit computation, claim forms (CF2–CF5) and eClaims transmission").grid(
            row=0, column=0, sticky="ew", pady=(0, 8)
        )
        tabs = ctk.CTkTabview(self, fg_color=Theme.CARD_BG,
                              border_width=1, border_color=Theme.BORDER)
        tabs.grid(row=1, column=0, sticky="nsew")
        tabs.add("Benefit Computation")
        tabs.add("Claim Forms")
        tabs.add("eClaims")

        self._build_computation_tab(tabs.tab("Benefit Computation"))
        self._build_claim_forms_tab(tabs.tab("Claim Forms"))
        self._build_eclaims_tab(tabs.tab("eClaims"))

    # ── TAB 1 – Benefit Computation ───────────────────────────────────────────
    def _build_computation_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        form = ctk.CTkFrame(parent, fg_color=Theme.CARD_BG,
                            corner_radius=Theme.CORNER_RADIUS,
                            border_width=1, border_color=Theme.BORDER)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure((0, 1, 2), weight=1)

        patients    = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]

        self.patient_field = FormField(form, "Patient", "combo",
                                       patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        self.rate_field = SearchPickerField(
            form,
            "Case Rate",
            label_fn=lambda r: f"{r.id} - {r.case_code}: {r.case_description}",
            dialog_title="Select Case Rate",
            columns=("Type", "Code", "Description", "Rate"),
            row_fn=lambda r: (
                r.case_type,
                r.case_code,
                r.case_description,
                f"₱{float(r.case_rate):,.2f}",
            ),
            search_fn=lambda q, ft, page, pp: self.service.search_rates(q, ft, page, pp),
            filter_options=["All", "Medical", "Surgical"],
        )
        self.rate_field.grid(row=0, column=1, sticky="ew", padx=16, pady=16)
        self.bill_field = FormField(form, "Total Bill Amount")
        self.bill_field.set("0")
        self.bill_field.grid(row=0, column=2, sticky="ew", padx=16, pady=16)

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 16))
        ActionButton(btn_row, text="Compute Benefits",
                     command=self._compute).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Process Transaction", style="success",
                     command=self._process).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="View History", style="secondary",
                     command=self._load_history).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Print Summary PDF", style="secondary",
                     command=self._print_summary).pack(side="left")

        summary_frame = ctk.CTkFrame(parent, fg_color=Theme.CARD_BG,
                                     corner_radius=Theme.CORNER_RADIUS,
                                     border_width=1, border_color=Theme.BORDER)
        summary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.summary_labels = {}
        summary_items = [
            "case_rate_amount", "hospital_share", "professional_fee",
            "philhealth_deduction", "senior_discount", "pwd_discount",
            "patient_balance",
        ]
        for i, key in enumerate(summary_items):
            lbl = ctk.CTkLabel(
                summary_frame,
                text=f"{key.replace('_', ' ').title()}: ₱0.00",
                font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY, anchor="w",
            )
            lbl.grid(row=i // 2, column=i % 2, sticky="w", padx=20, pady=8)
            self.summary_labels[key] = lbl

        self.history_table = DataTable(
            parent,
            ["Date", "Case Code", "PhilHealth Deduction", "Patient Balance", "Total Bill"],
        )
        self.history_table.grid(row=2, column=0, sticky="nsew")

    # ── TAB 2 – Claim Forms ───────────────────────────────────────────────────
    def _build_claim_forms_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # ── Row 1: New form buttons ────────────────────────────────────────
        new_row = ctk.CTkFrame(parent, fg_color=Theme.ACCENT_LIGHT,
                               corner_radius=8, border_width=1,
                               border_color=Theme.BORDER)
        new_row.grid(row=0, column=0, sticky="ew", pady=(8, 4))
        ctk.CTkLabel(new_row, text="New Form:", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(12, 8), pady=8)

        form_colors = {
            "CF1": ("primary", "CF1 – Member Info"),
            "CF2": ("success",  "CF2 – Hospital"),
            "CF3": ("primary",  "CF3 – Clinical Record"),
            "CF4": ("success",  "CF4 – Outpatient"),
            "CF5": ("primary",  "CF5 – Dialysis"),
            "CSF": ("success",  "CSF – Signature"),
        }
        for ft, (style, label) in form_colors.items():
            ActionButton(new_row, text=f"+ {label}", style=style, height=34,
                         command=lambda f=ft: self._open_new_form_dialog(f)
                         ).pack(side="left", padx=3, pady=6)

        # ── Row 2: Action buttons ──────────────────────────────────────────
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        ActionButton(toolbar, text="View Details",
                     command=self._view_form_details).pack(side="left", padx=(0, 6))
        ActionButton(toolbar, text="Transmit eClaim",
                     command=self._open_eclaim_dialog).pack(side="left", padx=(0, 6))
        ActionButton(toolbar, text="Print PDF", style="secondary",
                     command=self._print_selected_form).pack(side="left", padx=(0, 6))
        ctk.CTkFrame(toolbar, fg_color=Theme.BORDER, width=1
                     ).pack(side="left", fill="y", padx=8)
        ActionButton(toolbar, text="Mark Submitted",
                     command=lambda: self._set_status("Submitted")).pack(side="left", padx=(0, 6))
        ActionButton(toolbar, text="Mark Approved", style="success",
                     command=lambda: self._set_status("Approved")).pack(side="left", padx=(0, 6))
        ActionButton(toolbar, text="Delete Draft", style="danger",
                     command=self._delete_form).pack(side="left", padx=(0, 6))
        ActionButton(toolbar, text="Refresh", style="secondary",
                     command=self._load_claim_forms).pack(side="left")

        self.cf_table = DataTable(
            parent,
            ["Form No.", "Type", "Patient", "Date", "Diagnosis",
             "Case Rate (As of)", "Amount Claimed", "Status", "eClaim Status"],
        )
        self.cf_table.grid(row=2, column=0, sticky="nsew")
        parent.grid_rowconfigure(2, weight=1)
        self._load_claim_forms()

    # ── TAB 3 – eClaims Log ───────────────────────────────────────────────────
    def _build_eclaims_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # Info banner
        info = ctk.CTkFrame(parent, fg_color=Theme.ACCENT_LIGHT,
                            corner_radius=Theme.CORNER_RADIUS,
                            border_width=1, border_color=Theme.BORDER)
        info.grid(row=0, column=0, sticky="ew", pady=(8, 8))
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info,
            text=(
                "eClaims Transmission Log  —  Select a claim and click 'Transmit eClaim' in the Claim Forms tab to bundle "
                "supporting PDFs and generate a submission package for PhilHealth eClaims portal."
            ),
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY,
            anchor="w", wraplength=900, justify="left",
        ).pack(padx=16, pady=10)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ActionButton(toolbar, text="Refresh", style="secondary",
                     command=self._load_eclaims).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Mark Acknowledged", style="success",
                     command=lambda: self._set_eclaim_status("Acknowledged")
                     ).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Mark Rejected", style="danger",
                     command=lambda: self._set_eclaim_status("Rejected")
                     ).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Open Package Folder", style="secondary",
                     command=self._open_eclaim_package).pack(side="left")

        self.eclaim_table = DataTable(
            parent,
            ["Form No.", "Type", "Patient", "PhilHealth No.",
             "Case Rate (As of)", "Amount Claimed", "eClaim Ref No.",
             "Transmitted At", "eClaim Status"],
        )
        self.eclaim_table.grid(row=2, column=0, sticky="nsew")
        parent.grid_rowconfigure(2, weight=1)
        self._load_eclaims()

    # ── Computation helpers ───────────────────────────────────────────────────
    def _parse_ids(self) -> tuple:
        try:
            patient_id = int(self.patient_field.get().split(" - ")[0])
        except (ValueError, IndexError):
            return None, None
        rate = self.rate_field.get_item()
        rate_id = rate.id if rate else None
        return patient_id, rate_id

    def _compute(self) -> None:
        patient_id, rate_id = self._parse_ids()
        if not patient_id or not rate_id:
            show_message(self, "Validation", "Select patient and case rate.", "warning")
            return
        try:
            total_bill = Decimal(self.bill_field.get())
        except Exception:
            show_message(self, "Validation", "Enter valid bill amount.", "warning")
            return
        self.computation = self.service.compute_benefits(patient_id, rate_id, total_bill)
        if not self.computation:
            show_message(self, "Error", "Unable to compute benefits.", "error")
            return
        for key, lbl in self.summary_labels.items():
            val = self.computation.get(key, Decimal("0"))
            lbl.configure(text=f"{key.replace('_', ' ').title()}: {format_currency(val)}")

    def _process(self) -> None:
        if not self.computation:
            self._compute()
        patient_id, rate_id = self._parse_ids()
        if not patient_id or not rate_id:
            return
        total_bill = Decimal(self.bill_field.get())
        ok, msg, _ = self.service.process_transaction(patient_id, rate_id, total_bill)
        show_message(self, "PhilHealth", msg, "success" if ok else "error")
        if ok:
            self._load_history()

    def _load_history(self) -> None:
        patient_id, _ = self._parse_ids()
        if not patient_id:
            return
        transactions = self.service.get_patient_history(patient_id)
        self.history_table.clear_rows()
        for t in transactions:
            code = t.case_rate.case_code if t.case_rate else "—"
            self.history_table.add_row([
                str(t.transaction_date)[:10], code,
                format_currency(t.philhealth_deduction),
                format_currency(t.patient_balance),
                format_currency(t.total_bill),
            ])

    def _print_summary(self) -> None:
        if not self.computation:
            show_message(self, "Info", "Compute benefits first.", "warning")
            return
        patient_id, rate_id = self._parse_ids()
        if not patient_id:
            return
        patient = self.patient_service.get_by_id(patient_id)
        rates   = self.service.get_case_rates()
        rate    = next((r for r in rates if r.id == rate_id), None)
        if not patient or not rate:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=f"PhilHealth_Summary_{patient.last_name}.pdf",
        )
        if not path:
            return
        PDFGenerator.generate_philhealth_summary(
            output_path=path, clinic_name=self._get_clinic_name(),
            patient_name=patient.full_name,
            philhealth_number=patient.philhealth_number or "—",
            case_description=rate.case_description,
            computation=self.computation,
        )
        show_message(self, "PDF", "PhilHealth summary saved.", "success")
        os.startfile(path)

    # ── Claim form helpers ────────────────────────────────────────────────────
    @staticmethod
    def _truncate(text: str, limit: int = 45) -> str:
        if not text:
            return "—"
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _format_claim_date(self, form) -> str:
        d = form.date_of_claim
        if not d and form.created_at:
            d = form.created_at.date() if isinstance(form.created_at, datetime) else form.created_at
        return format_date(d) if d else "—"

    def _format_case_rate(self, form) -> str:
        code = (form.case_rate_code or "").strip()
        if not code:
            return "—"
        rate = self.service.rate_repo.get_by_code(code)
        if not rate:
            return code
        as_of = format_price_as_of(rate.price_effective_date)
        return f"₱{float(rate.case_rate):,.2f} (as of {as_of})"

    def _load_claim_forms(self) -> None:
        forms = self.service.get_all_claim_forms()
        self.cf_table.clear_rows()
        for f in forms:
            patient_name  = f.patient.full_name if f.patient else "—"
            eclaim_status = getattr(f, "eclaim_status", "Pending") or "Pending"
            self.cf_table.add_row([
                f.form_number,
                f.form_type,
                patient_name,
                self._format_claim_date(f),
                self._truncate(f.diagnosis or "—"),
                self._format_case_rate(f),
                format_currency(f.total_amount_claimed),
                f.status,
                eclaim_status,
            ])

    def _get_patients_list(self) -> list:
        return [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]

    def _view_form_details(self) -> None:
        form = self._selected_form()
        if not form:
            return
        _ViewClaimDialog(self, form=form)

    def _open_new_form_dialog(self, form_type: str) -> None:
        patients = self._get_patients_list()
        fns = {
            "CF1": _CF1Dialog,
            "CF2": _CF2Dialog,
            "CF3": _CF3Dialog,
            "CF4": _CF4Dialog,
            "CF5": _CF5Dialog,
            "CSF": _CSFDialog,
        }
        fn = fns.get(form_type)
        if fn:
            fn(self, patients, self.service, self._load_claim_forms)

    def _selected_form(self):
        selected = self.cf_table.get_selected_row()
        if not selected:
            show_message(self, "Selection", "Please select a claim form first.", "warning")
            return None
        form = self.service.claim_form_repo.get_by_number(selected[0])
        if not form:
            show_message(self, "Error", "Claim form not found.", "error")
        return form

    def _set_status(self, status: str) -> None:
        form = self._selected_form()
        if not form:
            return
        ok, msg = self.service.update_claim_form_status(form.id, status)
        show_message(self, "Status", msg, "success" if ok else "error")
        if ok:
            self._load_claim_forms()

    def _delete_form(self) -> None:
        form = self._selected_form()
        if not form:
            return
        ok, msg = self.service.delete_claim_form(form.id)
        show_message(self, "Delete", msg, "success" if ok else "error")
        if ok:
            self._load_claim_forms()

    def _open_eclaim_dialog(self) -> None:
        form = self._selected_form()
        if not form:
            return
        clinic_info = {
            "clinic_name":   self._get_clinic_name(),
            "clinic_address": self._get_clinic_address(),
            "accreditation": self._get_accreditation(),
        }
        _EClaimTransmitDialog(
            self, form=form,
            philhealth_service=self.service,
            clinic_info=clinic_info,
            on_transmitted=lambda: (self._load_claim_forms(), self._load_eclaims()),
        )

    def _print_selected_form(self) -> None:
        form = self._selected_form()
        if not form:
            return
        patient = form.patient
        if not patient:
            show_message(self, "Error", "Patient data missing.", "error")
            return

        safe_name = "".join(c for c in patient.full_name if c not in '\\/:*?"<>|')
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=f"{safe_name} - {form.form_type}.pdf",
        )
        if not path:
            return

        clinic  = self._get_clinic_name()
        addr    = self._get_clinic_address()
        accred  = self._get_accreditation()

        try:
            self._generate_form_pdf(form, path, clinic, addr, accred)
            show_message(self, "PDF", f"{form.form_type} form saved.", "success")
            os.startfile(path)
        except Exception as exc:
            show_message(self, "PDF Error", str(exc), "error")

    def _generate_form_pdf(self, form, path, clinic, addr, accred) -> None:
        ft      = form.form_type
        patient = form.patient
        pname   = patient.full_name if patient else "—"
        ph_num  = form.philhealth_number or "—"
        mem_tp  = (patient.philhealth_member_type if patient else None) or "—"
        adm_dx  = getattr(form, "admission_diagnosis", None) or form.diagnosis or "—"
        disp    = getattr(form, "patient_disposition", None) or "—"
        t_adm   = getattr(form, "time_admitted", None) or "—"
        t_dis   = getattr(form, "time_discharged", None) or "—"
        acc_tp  = getattr(form, "accommodation_type", None) or "—"
        physn   = getattr(form, "attending_physician", None) or "—"
        cr2     = getattr(form, "second_case_rate_code", None) or "—"
        ref_hci = getattr(form, "referring_hci", None) or "—"

        common = dict(
            output_path=path, clinic_name=clinic, clinic_address=addr,
            accreditation_no=accred, form_number=form.form_number,
            patient_name=pname, philhealth_number=ph_num, member_type=mem_tp,
            diagnosis=form.diagnosis or "—", icd_code=form.icd_code or "—",
            case_rate_code=form.case_rate_code or "—",
            second_case_rate_code=cr2,
            total_claimed=float(form.total_amount_claimed or 0),
            date_of_claim=str(form.date_of_claim or date.today()),
            notes=form.notes or "",
        )

        if ft in ("CF2", "CF4"):
            PDFGenerator.generate_cf2_cf4(
                **common,
                form_type=ft,
                admission_date=str(form.admission_date or "—"),
                discharge_date=str(form.discharge_date or "—"),
                time_admitted=t_adm, time_discharged=t_dis,
                type_of_admission=form.type_of_admission or "Ordinary",
                patient_disposition=disp, accommodation_type=acc_tp,
                admission_diagnosis=adm_dx, referring_hci=ref_hci,
                attending_physician=physn,
                room_charges=float(form.room_charges or 0),
                medicine_charges=float(form.medicine_charges or 0),
                xray_lab_charges=float(form.xray_lab_charges or 0),
                other_charges=float(form.other_charges or 0),
                hospital_share=float(form.hospital_share or 0),
            )
        elif ft == "CF3":
            PDFGenerator.generate_cf3(
                **common,
                admission_date=str(form.admission_date or "—"),
                discharge_date=str(form.discharge_date or "—"),
                time_admitted=t_adm, time_discharged=t_dis,
                patient_disposition=disp, attending_physician=physn,
                physician_prc_no=form.physician_prc_no or "—",
                physician_ptr_no=form.physician_ptr_no or "—",
                physician_philhealth_no=form.physician_philhealth_no or "—",
            )
        elif ft == "CF5":
            PDFGenerator.generate_cf5(
                **common,
                dialysis_center_name=form.dialysis_center_name or clinic,
                dialysis_center_accreditation=form.dialysis_center_accreditation or accred,
                dialysis_type=form.dialysis_type or "Hemodialysis",
                period_from=str(form.period_from or "—"),
                period_to=str(form.period_to or "—"),
                number_of_sessions=form.number_of_sessions or 0,
            )
        elif ft in ("CF1", "CSF"):
            PDFGenerator.generate_cf1_csf(
                **common,
                form_type=ft,
                admission_date=str(form.admission_date or "—"),
                discharge_date=str(form.discharge_date or "—"),
            )
        else:
            PDFGenerator.generate_cf2_cf4(**common, form_type=ft,
                admission_date="—", discharge_date="—", time_admitted="—",
                time_discharged="—", type_of_admission="—",
                patient_disposition="—", accommodation_type="—",
                admission_diagnosis="—", referring_hci="—",
                attending_physician="—",
                room_charges=0, medicine_charges=0, xray_lab_charges=0,
                other_charges=0, hospital_share=0)

    # ── eClaims tab helpers ───────────────────────────────────────────────────
    def _load_eclaims(self) -> None:
        forms = self.service.get_all_claim_forms()
        self.eclaim_table.clear_rows()
        for f in forms:
            patient_name  = f.patient.full_name if f.patient else "—"
            eclaim_status = getattr(f, "eclaim_status", "Pending") or "Pending"
            eclaim_ref    = getattr(f, "eclaim_ref_no", None) or "—"
            submitted     = getattr(f, "eclaim_submitted_at", None)
            eclaim_date   = format_datetime(submitted) if submitted else "—"
            self.eclaim_table.add_row([
                f.form_number,
                f.form_type,
                patient_name,
                f.philhealth_number or "—",
                self._format_case_rate(f),
                format_currency(f.total_amount_claimed),
                eclaim_ref,
                eclaim_date,
                eclaim_status,
            ])

    def _set_eclaim_status(self, status: str) -> None:
        selected = self.eclaim_table.get_selected_row()
        if not selected:
            show_message(self, "Selection", "Select a claim first.", "warning")
            return
        form = self.service.claim_form_repo.get_by_number(selected[0])
        if not form:
            return
        ok, msg = self.service.update_eclaim_status(form.id, status)
        show_message(self, "eClaim Status", msg, "success" if ok else "error")
        if ok:
            self._load_eclaims()

    def _open_eclaim_package(self) -> None:
        selected = self.eclaim_table.get_selected_row()
        if not selected:
            show_message(self, "Selection", "Select a claim first.", "warning")
            return
        form_number = selected[0]
        pkg_folder  = Path(ECLAIMS_DIR) / form_number
        if pkg_folder.exists():
            os.startfile(str(pkg_folder))
        else:
            zip_path = Path(ECLAIMS_DIR) / f"{form_number}.zip"
            if zip_path.exists():
                os.startfile(str(zip_path.parent))
            else:
                show_message(self, "Not Found",
                             "No package found. Transmit the claim first.", "warning")

    # ── Clinic info helpers ───────────────────────────────────────────────────
    def _get_clinic_name(self) -> str:
        if self.settings_service:
            s = self.settings_service.get_settings()
            return s.clinic_name or "Clinic"
        return "Clinic"

    def _get_clinic_address(self) -> str:
        if self.settings_service:
            s = self.settings_service.get_settings()
            return s.clinic_address or ""
        return ""

    def _get_accreditation(self) -> str:
        if self.settings_service:
            s = self.settings_service.get_settings()
            return s.philhealth_accreditation or ""
        return ""

    def refresh(self) -> None:
        pass
