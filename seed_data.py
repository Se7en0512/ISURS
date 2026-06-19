"""
seed_data.py — PULSE Database Seeder
Generates realistic Philippine hospital data for testing.
Run: python seed_data.py
"""
import os, sys, random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import app, db
from app import Store, Unit, Ward, Section, Item, Week, Report
from app import Equipment, EquipmentLog, EquipmentMovement, Staff, ActivityLog

random.seed(42)

PHI_FIRST = [
    'Maria', 'Jose', 'Juan', 'Ana', 'Pedro', 'Luisa', 'Carlos', 'Rosa',
    'Antonio', 'Elena', 'Miguel', 'Carmen', 'Francisco', 'Teresa', 'Ramon',
    'Gloria', 'Eduardo', 'Luzviminda', 'Felipe', 'Marlon', 'Cristina', 'Dante',
    'Marites', 'Roderick', 'Sheryl', 'Gilbert', 'Jennifer', 'Eddie', 'Ginalyn',
    'Reynaldo', 'Aileen', 'Nelson', 'Maricel', 'Dominador', 'Rowena'
]

PHI_LAST = [
    'Santos', 'Reyes', 'Cruz', 'Bautista', 'Gonzales', 'Mendoza', 'Garcia',
    'Tolentino', 'Aquino', 'Castillo', 'Villanueva', 'David', 'Fernandez',
    'Gutierrez', 'Dela Cruz', 'Roman', 'Palacios', 'Rivera', 'Soriano',
    'Manaloto', 'Villegas', 'Navarro', 'Salcedo', 'Esguerra', 'Lazaro',
    'Magtoto', 'Pascual', 'Santiago', 'Alcantara', 'Dimagiba', 'Barrera',
    'Lingatong', 'Abella', 'Carreon', 'Zamora'
]

POSITIONS = {
    'admin': ['System Administrator', 'IT Manager', 'Chief of Hospital'],
    'doctor': ['Resident Physician', 'Consultant', 'Chief of Medicine', 'Surgeon'],
    'nurse': ['Staff Nurse', 'Head Nurse', 'Clinical Nurse', 'Nurse Supervisor'],
    'tech': ['Medical Technologist', 'Radiologic Technologist', 'Pharmacist', 'Biomedical Engineer'],
}

DEPARTMENTS = ['Emergency', 'ICU', 'OPD', 'Pediatrics', 'Maternity', 'General Ward', 'Pharmacy', 'Laboratory', 'Biomedical']

STORE_NAMES = ['Main Pharmacy', 'ER Supply Room', 'ICU Stockroom', 'Central Supply', 'OPD Pharmacy', 'General Store']

UNIT_NAMES = ['Emergency Unit', 'Intensive Care', 'Outpatient', 'Pediatrics', 'Maternity']

WARD_NAMES = {
    'Emergency Unit': ['ER Triage', 'ER Treatment Bay', 'ER Observation'],
    'Intensive Care': ['ICU-Medical', 'ICU-Surgical', 'NICU'],
    'Outpatient': ['OPD Consultation', 'OPD Procedure Room', 'OPD Waiting'],
    'Pediatrics': ['Pedia Ward', 'Pedia Isolation', 'Pedia Play Area'],
    'Maternity': ['Labor & Delivery', 'Postpartum Ward', 'Nursery'],
}

SECTION_NAMES = ['Pharmacy', 'Central Supply', 'Biomedical', 'Laboratory', 'Nutrition']

ITEMS_DATA = [
    ('PARA-001', 'Paracetamol 500mg Tablet', 0, 100),
    ('PARA-002', 'Paracetamol 250mg/5mL Suspension', 1, 30),
    ('AMOX-001', 'Amoxicillin 500mg Capsule', 0, 80),
    ('AMOX-002', 'Amoxicillin 250mg/5mL Suspension', 1, 25),
    ('CEF-001', 'Cefuroxime 750mg Injection', 2, 40),
    ('CEF-002', 'Ceftriaxone 1g Injection', 2, 35),
    ('NS-001', 'Normal Saline 500mL IV', 0, 60),
    ('NS-002', 'Normal Saline 1L IV', 0, 50),
    ('D5W-001', 'D5W 500mL IV', 0, 45),
    ('D5W-002', 'D5W 1L IV', 3, 40),
    ('SYR-001', 'Syringe 3mL with Needle', 3, 500),
    ('SYR-002', 'Syringe 5mL with Needle', 3, 400),
    ('SYR-003', 'Syringe 10mL with Needle', 3, 300),
    ('NEED-001', 'Needle 23G x 1"', 3, 500),
    ('NEED-002', 'Needle 21G x 1.5"', 3, 400),
    ('GLOV-001', 'Latex Exam Gloves (Small)', 3, 1000),
    ('GLOV-002', 'Latex Exam Gloves (Medium)', 3, 2000),
    ('GLOV-003', 'Latex Exam Gloves (Large)', 3, 1500),
    ('MASK-001', 'Surgical Face Mask (Box/50)', 0, 200),
    ('MASK-002', 'N95 Respirator Mask', 0, 100),
    ('ALC-001', 'Isopropyl Alcohol 70% 500mL', 1, 80),
    ('ALC-002', 'Isopropyl Alcohol 70% 1L', 1, 60),
    ('BET-001', 'Betadine Solution 120mL', 1, 40),
    ('BET-002', 'Betadine Scrub 500mL', 1, 30),
    ('BAND-001', 'Gauze Bandage 4"x4" (Box/100)', 3, 80),
    ('BAND-002', 'Elastic Bandage 4"x5yd', 3, 50),
    ('BAND-003', 'Adhesive Tape 1" (Roll)', 3, 60),
    ('CATH-001', 'Foley Catheter 18Fr', 2, 25),
    ('CATH-002', 'Foley Catheter 20Fr', 2, 20),
    ('TUBE-001', 'NG Tube 16Fr', 1, 15),
    ('TUBE-002', 'Endotracheal Tube 7.5mm', 2, 10),
    ('BAG-001', 'Urine Collection Bag 2L', 3, 30),
    ('GOWN-001', 'Disposable Isolation Gown', 3, 100),
    ('CAP-001', 'Surgical Cap (Box/100)', 3, 50),
    ('O2-001', 'Oxygen Mask Adult', 2, 25),
    ('O2-002', 'Nasal Cannula Adult', 2, 30),
    ('IV-001', 'IV Set (Standard)', 0, 80),
    ('IV-002', 'IV Set (Micro drip)', 0, 40),
    ('BUT-001', 'Butterfly Needle 23G', 0, 50),
    ('BLOOD-001', 'Blood Transfusion Set', 2, 15),
    ('SCAL-001', 'Scalpel Blade #11 (Box/100)', 3, 20),
    ('SCAL-002', 'Scalpel Blade #15 (Box/100)', 3, 15),
    ('SUT-001', 'Silk Suture 2-0 (Box/12)', 2, 10),
    ('SUT-002', 'Nylon Suture 3-0 (Box/12)', 2, 8),
    ('HEPA-001', 'Heparin Lock 5mL', 1, 20),
    ('DEXT-001', 'Dextrose 50% 50mL Ampule', 0, 25),
    ('VIT-001', 'Vitamin B Complex Injection', 0, 30),
    ('KCL-001', 'KCl 20mEq/10mL Ampule', 0, 20),
]

EQUIPMENT_DATA = [
    ('BP-001', 'Digital BP Apparatus', 'WORKING', 'ER Triage'),
    ('BP-002', 'Manual BP Apparatus (Adult)', 'WORKING', 'ICU-Medical'),
    ('BP-003', 'Manual BP Apparatus (Pedia)', 'WORKING', 'Pedia Ward'),
    ('OX-001', 'Pulse Oximeter (Handheld)', 'WORKING', 'ER Treatment Bay'),
    ('OX-002', 'Pulse Oximeter (Portable)', 'WORKING', 'ICU-Medical'),
    ('OX-003', 'Pulse Oximeter (Pedia)', 'WORKING', 'NICU'),
    ('NEB-001', 'Nebulizer (Compressor)', 'WORKING', 'ER Treatment Bay'),
    ('NEB-002', 'Nebulizer (Ultrasonic)', 'WORKING', 'OPD Procedure Room'),
    ('NEB-003', 'Nebulizer (Portable)', 'MISSING', 'OPD Consultation'),
    ('ECG-001', '12-Lead ECG Machine', 'WORKING', 'ER Triage'),
    ('ECG-002', 'Holter Monitor', 'MAINTENANCE', 'ICU-Medical'),
    ('DEF-001', 'Defibrillator (AED)', 'WORKING', 'ER Triage'),
    ('DEF-002', 'Defibrillator (Manual)', 'WORKING', 'ICU-Surgical'),
    ('VENT-001', 'Ventilator (Adult)', 'WORKING', 'ICU-Medical'),
    ('VENT-002', 'Ventilator (Neonatal)', 'WORKING', 'NICU'),
    ('SUCT-001', 'Suction Machine', 'WORKING', 'ER Treatment Bay'),
    ('SUCT-002', 'Suction Machine (Portable)', 'WORKING', 'ICU-Surgical'),
    ('INF-001', 'Infusion Pump', 'WORKING', 'ICU-Medical'),
    ('INF-002', 'Infusion Pump', 'WORKING', 'ICU-Surgical'),
    ('INF-003', 'Infusion Pump', 'LOANED', 'ER Triage'),
    ('SYR-001', 'Syringe Pump', 'WORKING', 'ICU-Medical'),
    ('SYR-002', 'Syringe Pump', 'WORKING', 'NICU'),
    ('BED-001', 'Hospital Bed (Electric)', 'WORKING', 'General Ward'),
    ('BED-002', 'Hospital Bed (Manual)', 'CONDEMNED', 'General Ward'),
    ('BED-003', 'Stretcher (Wheeled)', 'WORKING', 'ER Triage'),
    ('WCH-001', 'Wheelchair', 'WORKING', 'OPD Waiting'),
    ('WCH-002', 'Wheelchair (Bariatric)', 'WORKING', 'OPD Waiting'),
    ('WAR-001', 'Warming Cabinet', 'WORKING', 'Nursery'),
    ('PHOT-001', 'Phototherapy Light', 'WORKING', 'Nursery'),
    ('INC-001', 'Incubator (Neonatal)', 'WORKING', 'NICU'),
]

STAFF_DATA = [
    ('ADMIN', 'System Administrator', 'IT Department', 'System Administrator', 'admin'),
    ('DOC001', 'Dr. Maria Clara Santos', 'Emergency', 'Chief of Medicine', 'staff'),
    ('DOC002', 'Dr. Jose Rizal Reyes', 'ICU', 'Consultant', 'staff'),
    ('DOC003', 'Dr. Juan Luna Cruz', 'Pediatrics', 'Resident Physician', 'staff'),
    ('DOC004', 'Dr. Rosa Tanglaw Bautista', 'Maternity', 'Surgeon', 'staff'),
    ('NSE001', 'Nurse Joy Cruz', 'Emergency', 'Head Nurse', 'staff'),
    ('NSE002', 'Nurse Pedro Gonzales', 'ICU', 'Clinical Nurse', 'staff'),
    ('NSE003', 'Nurse Ana Marie Mendoza', 'OPD', 'Staff Nurse', 'staff'),
    ('NSE004', 'Nurse Carlos Dela Torre', 'Pediatrics', 'Staff Nurse', 'staff'),
    ('NSE005', 'Nurse Elena Rivera', 'Maternity', 'Nurse Supervisor', 'staff'),
    ('NSE006', 'Nurse Miguel Villanueva', 'General Ward', 'Staff Nurse', 'staff'),
    ('NSE007', 'Nurse Luisa Mae Soriano', 'Emergency', 'Staff Nurse', 'staff'),
    ('NSE008', 'Nurse Antonio Castillo', 'ICU', 'Staff Nurse', 'staff'),
    ('NSE009', 'Nurse Teresa David', 'OPD', 'Staff Nurse', 'staff'),
    ('NSE010', 'Nurse Ramon Fernandez', 'General Ward', 'Staff Nurse', 'staff'),
    ('TEC001', 'MedTech Felipe Alcantara', 'Laboratory', 'Medical Technologist', 'staff'),
    ('TEC002', 'MedRadiology Gloria Santos', 'Laboratory', 'Radiologic Technologist', 'staff'),
    ('TEC003', 'Rx Cristina Lopez', 'Pharmacy', 'Pharmacist', 'staff'),
    ('TEC004', 'Biomed Engr. Eduardo Tan', 'Biomedical', 'Biomedical Engineer', 'staff'),
    ('TEC005', 'MedTech Marites Reyes', 'Laboratory', 'Medical Technologist', 'staff'),
    ('TEC006', 'Rx Roderick Cruz', 'Pharmacy', 'Pharmacist', 'staff'),
]

def seed():
    print('=== PULSE Database Seeder ===')
    print(f'Time range: Jan 2024 – Jun 2026')
    print()

    with app.app_context():
        # ─── Clear existing data ───
        print('Clearing existing data...')
        ActivityLog.query.delete()
        EquipmentMovement.query.delete()
        EquipmentLog.query.delete()
        Report.query.delete()
        Item.query.delete()
        Equipment.query.delete()
        Staff.query.delete()
        Week.query.delete()
        Ward.query.delete()
        Section.query.delete()
        Unit.query.delete()
        Store.query.delete()
        db.session.commit()

        # ─── Stores ───
        print('Creating stores...')
        stores = {}
        for name in STORE_NAMES:
            s = Store(name=name)
            db.session.add(s)
            stores[name] = s
        db.session.flush()

        # ─── Units & Wards ───
        print('Creating units & wards...')
        units = {}
        wards = {}
        for uname in UNIT_NAMES:
            u = Unit(name=uname)
            db.session.add(u)
            units[uname] = u
        db.session.flush()
        for uname, wnames in WARD_NAMES.items():
            for wname in wnames:
                w = Ward(name=wname, unit_id=units[uname].id)
                db.session.add(w)
                wards[wname] = w
        db.session.flush()

        # ─── Sections ───
        print('Creating sections...')
        sections = {}
        for sname in SECTION_NAMES:
            sec = Section(name=sname)
            db.session.add(sec)
            sections[sname] = sec
        db.session.flush()

        # ─── Weeks ───
        print('Creating weeks...')
        for wn in range(1, 53):
            w = Week(week_number=wn, date_range=f'Week {wn}')
            db.session.add(w)
        db.session.flush()

        # ─── Items ───
        print('Creating items...')
        items = []
        store_keys = list(stores.keys())
        for code, name, store_idx, critical in ITEMS_DATA:
            store_name = store_keys[store_idx]
            item = Item(
                code=code, name=name,
                store_id=stores[store_name].id,
                stock_quantity=random.randint(5, critical * 3 + 50),
                critical_level=critical,
            )
            db.session.add(item)
            items.append(item)
        db.session.flush()
        item_ids = [i.id for i in items]
        print(f'  {len(items)} items created')

        # ─── Equipment ───
        print('Creating equipment...')
        equipments = []
        base_date = datetime(2023, 6, 1)
        for biomed, name, status, location in EQUIPMENT_DATA:
            if status == 'WORKING':
                ls = base_date + timedelta(days=random.randint(30, 365))
                ns = ls + timedelta(days=random.randint(60, 180))
            elif status == 'MAINTENANCE':
                ls = base_date + timedelta(days=random.randint(300, 420))
                ns = datetime.now() - timedelta(days=random.randint(5, 30))
            else:
                ls = base_date + timedelta(days=random.randint(60, 200))
                ns = ls + timedelta(days=random.randint(90, 200))
            eq = Equipment(
                biomed=biomed, name=name, status=status, location=location,
                last_service_date=ls, next_service_date=ns,
            )
            db.session.add(eq)
            equipments.append(eq)
        db.session.flush()
        eq_ids = [e.id for e in equipments]
        print(f'  {len(equipments)} equipment created')

        # ─── Staff ───
        print('Creating staff...')
        staff_list = []
        ward_keys = list(wards.keys())
        for eid, name, dept, pos, role in STAFF_DATA:
            s = Staff(
                employee_id=eid, full_name=name, department=dept,
                position=pos, role=role, approved=True,
                password_hash=generate_password_hash('password123'),
            )
            db.session.add(s)
            staff_list.append(s)
        db.session.flush()
        staff_eids = [s.employee_id for s in staff_list]
        print(f'  {len(staff_list)} staff created')

        # ─── Reports (Jan 2024 – Jun 2026) ───
        print('Creating reports...')
        status_choices = ['Shortage', 'Not Available', 'Available', 'Partial']
        report_count = 0
        start = datetime(2024, 1, 1)
        end = datetime(2026, 6, 30)
        total_days = (end - start).days

        unit_ids = [u.id for u in Unit.query.all()]
        ward_ids = [w.id for w in Ward.query.all()]
        section_ids = [s.id for s in Section.query.all()]

        for day_offset in range(0, total_days + 1, 3):
            date = start + timedelta(days=day_offset)
            week_number = ((date - datetime(date.year, 1, 1)).days // 7) + 1
            if week_number > 52:
                week_number = 52
            week = Week.query.filter_by(week_number=week_number).first()
            if not week:
                continue

            # Generate between 2-8 reports per 3-day block
            reports_per_block = random.randint(2, 8)
            sampled_items = random.sample(item_ids, min(reports_per_block, len(item_ids)))
            for item_id in sampled_items:
                year_factor = (date.year - 2024) / 2.5
                r = random.random()
                if date.year == 2024:
                    weights = [0.35, 0.25, 0.20, 0.20]
                elif date.year == 2025:
                    weights = [0.25, 0.15, 0.35, 0.25]
                else:
                    weights = [0.20, 0.12, 0.38, 0.30]
                status = random.choices(status_choices, weights=weights, k=1)[0]
                # 10% chance to force Out-of-Stock for critical items
                if r < 0.10 and status == 'Shortage':
                    status = 'Not Available'

                rep = Report(
                    item_id=item_id,
                    week_id=week.id,
                    unit_id=random.choice(unit_ids),
                    ward_id=random.choice(ward_ids),
                    section_id=random.choice(section_ids),
                    status=status,
                    created_at=date + timedelta(
                        hours=random.randint(7, 17),
                        minutes=random.randint(0, 59),
                    ),
                )
                db.session.add(rep)
                report_count += 1
        db.session.flush()
        print(f'  {report_count} reports created')

        # ─── Equipment Logs & Movements ───
        print('Creating equipment logs & movements...')
        log_count = 0
        move_count = 0
        actions = ['ADDED', 'SCANNED', 'STATUS_CHANGED', 'CHECKED_OUT', 'CHECKED_IN']

        for eq_id in eq_ids:
            # 3-8 logs per equipment
            num_logs = random.randint(3, 8)
            for _ in range(num_logs):
                action = random.choice(actions)
                log_date = start + timedelta(
                    days=random.randint(0, total_days),
                    hours=random.randint(7, 17),
                )
                log = EquipmentLog(
                    equipment_id=eq_id, action=action,
                    scanned_by=random.choice(staff_eids),
                    notes=f'{action} during routine inspection',
                    created_at=log_date,
                )
                db.session.add(log)
                log_count += 1

            # 1-3 movements per equipment
            num_moves = random.randint(1, 3)
            for _ in range(num_moves):
                out_date = start + timedelta(
                    days=random.randint(0, total_days),
                    hours=random.randint(7, 17),
                )
                in_date = out_date + timedelta(
                    days=random.randint(1, 14),
                    hours=random.randint(7, 17),
                )
                move = EquipmentMovement(
                    equipment_id=eq_id,
                    checked_out_by=random.choice(staff_eids),
                    checked_in_by=random.choice(staff_eids),
                    source_location=f'Room {random.randint(101, 515)}',
                    destination=f'Room {random.randint(101, 515)}',
                    purpose=random.choice(['Patient use', 'Routine check', 'Transfer', 'Emergency use']),
                    checked_out_at=out_date,
                    checked_in_at=in_date if random.random() > 0.2 else None,
                    status='IN' if random.random() > 0.2 else 'OUT',
                )
                db.session.add(move)
                move_count += 1
        db.session.flush()
        print(f'  {log_count} equipment logs created')
        print(f'  {move_count} equipment movements created')

        # ─── Activity Log ───
        print('Creating activity logs...')
        activity_actions = ['Login', 'Logout', 'Settings', 'Registration', 'Import', 'Export', 'Quick Report']
        activity_count = 0
        for _ in range(50):
            al = ActivityLog(
                user=random.choice(staff_eids),
                action=random.choice(activity_actions),
                details=f'Activity log entry #{_ + 1}',
                created_at=start + timedelta(
                    days=random.randint(0, total_days),
                    hours=random.randint(7, 17),
                ),
            )
            db.session.add(al)
            activity_count += 1
        db.session.commit()
        print(f'  {activity_count} activity logs created')
        print()

        # ─── Summary ───
        print('=== Seed Complete ===')
        print(f'  Stores:        {len(stores)}')
        print(f'  Units:         {len(units)}')
        print(f'  Wards:         {len(wards)}')
        print(f'  Sections:      {len(sections)}')
        print(f'  Items:         {len(items)}')
        print(f'  Staff:         {len(staff_list)}')
        print(f'  Equipment:     {len(equipments)}')
        print(f'  Reports:       {report_count}')
        print(f'  Equip Logs:    {log_count}')
        print(f'  Equip Moves:   {move_count}')
        print(f'  Activity Logs: {activity_count}')
        print(f'  All passwords: password123')
        print()

if __name__ == '__main__':
    seed()
