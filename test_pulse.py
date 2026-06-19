"""
test_pulse.py — Comprehensive QA test for PULSE (Flask app).
Run: python test_pulse.py
"""
import os, sys, json, io, tempfile, unittest
from datetime import datetime, timedelta

# ── Test config: override before importing app ──
os.environ['PULSE_SECRET_KEY'] = 'test-secret-key-12345'

# Use a temporary directory for test database
_test_tmp = tempfile.mkdtemp()
os.environ['PULSE_DATA_DIR'] = _test_tmp

import app as pulse_app
app = pulse_app.app
db = pulse_app.db

# Test configuration overrides
app.config.update(
    TESTING=True,
    WTF_CSRF_ENABLED=False,
    SERVER_NAME='localhost',
    SESSION_COOKIE_DOMAIN=None,
)

# Disable rate limiter for testing
pulse_app.limiter.enabled = False

with app.app_context():
    from sqlalchemy import text
    db.create_all()
    from sqlalchemy import inspect as sa_inspect
    try:
        inspector = sa_inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('staff')]
        with db.engine.connect() as conn:
            if 'default_unit_id' not in cols:
                conn.execute(text("ALTER TABLE staff ADD COLUMN default_unit_id INTEGER REFERENCES unit(id)"))
            if 'default_ward_id' not in cols:
                conn.execute(text("ALTER TABLE staff ADD COLUMN default_ward_id INTEGER REFERENCES ward(id)"))
            conn.commit()
    except Exception:
        pass


class TestPulseApp(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.create_all()
            cls._seed_data()

    @classmethod
    def _seed_data(cls):
        """Minimal seed data for testing."""
        from app import Store, Unit, Ward, Section, Item, Week, Report, Equipment, EquipmentLog, Staff

        # Stores
        for n in ['Main Pharmacy', 'ER Supply Room', 'ICU Stockroom', 'Central Supply', 'OPD Pharmacy', 'General Store']:
            if not Store.query.filter_by(name=n).first():
                db.session.add(Store(name=n))

        # Unit + Wards
        u1 = Unit(name='Emergency Unit')
        u2 = Unit(name='Intensive Care')
        u3 = Unit(name='Outpatient')
        db.session.add_all([u1, u2, u3])
        db.session.flush()
        for u, wn in [(u1, 'ER Triage'), (u1, 'ER Treatment'), (u2, 'ICU-Medical'), (u2, 'ICU-Surgical')]:
            if not Ward.query.filter_by(name=wn, unit_id=u.id).first():
                db.session.add(Ward(name=wn, unit_id=u.id))

        # Sections
        for n in ['Pharmacy', 'Central Supply', 'Biomedical', 'Laboratory', 'Nutrition']:
            if not Section.query.filter_by(name=n).first():
                db.session.add(Section(name=n))

        db.session.commit()

        # Items
        items_data = [
            ('PARA-001', 'Paracetamol 500mg Tablet', 'Main Pharmacy', 500, 100),
            ('AMOX-001', 'Amoxicillin 500mg Capsule', 'Main Pharmacy', 300, 80),
            ('MASK-001', 'Surgical Face Mask (Box/50)', 'Main Pharmacy', 800, 200),
            ('SYR-001', 'Syringe 3mL with Needle', 'Central Supply', 2500, 500),
            ('GLOV-001', 'Latex Exam Gloves (Small)', 'Central Supply', 5000, 1000),
            ('NS-001', 'Normal Saline 500mL IV', 'Main Pharmacy', 0, 60),
            ('O2-001', 'Oxygen Mask Adult', 'ICU Stockroom', 10, 25),
        ]
        for code, name, store_name, sq, cl in items_data:
            store = Store.query.filter_by(name=store_name).first()
            if store and not Item.query.filter_by(code=code).first():
                db.session.add(Item(code=code, name=name, store_id=store.id, stock_quantity=sq, critical_level=cl))

        # Weeks
        for wn in range(1, 53):
            if not Week.query.filter_by(week_number=wn).first():
                db.session.add(Week(week_number=wn, date_range=f'2024-W{wn:02d}'))
        db.session.commit()

        # Reports
        week1 = Week.query.filter_by(week_number=1).first()
        item1 = Item.query.filter_by(code='PARA-001').first()
        item2 = Item.query.filter_by(code='MASK-001').first()
        unit1 = Unit.query.filter_by(name='Emergency Unit').first()
        ward1 = Ward.query.filter_by(name='ER Triage').first()
        section1 = Section.query.filter_by(name='Pharmacy').first()
        if week1 and item1 and unit1 and ward1 and section1:
            if not Report.query.filter_by(item_id=item1.id, week_id=week1.id).first():
                db.session.add(Report(item_id=item1.id, week_id=week1.id, unit_id=unit1.id,
                                      ward_id=ward1.id, section_id=section1.id, status='Shortage'))
            if item2 and not Report.query.filter_by(item_id=item2.id, week_id=week1.id).first():
                db.session.add(Report(item_id=item2.id, week_id=week1.id, unit_id=unit1.id,
                                      ward_id=ward1.id, section_id=section1.id, status='Not available'))
        db.session.commit()

        # Admin staff (pre-approved)
        admin = Staff(employee_id='ADMIN', full_name='System Admin', department='IT', position='Administrator')
        admin.set_password('password123')
        admin.approved = True
        admin.role = 'admin'
        db.session.add(admin)

        # Regular staff (approved)
        staff1 = Staff(employee_id='N001', full_name='Nurse One', department='ER', position='Nurse')
        staff1.set_password('password123')
        staff1.approved = True
        db.session.add(staff1)

        # Unapproved staff
        staff2 = Staff(employee_id='N002', full_name='Nurse Two', department='ER', position='Nurse')
        staff2.set_password('password123')
        staff2.approved = False
        db.session.add(staff2)
        db.session.commit()

        # Equipment
        equip_data = [
            ('BP-001', 'BP Apparatus Manual', 'WORKING', 'ER Room 1', ''),
            ('VENT-001', 'Ventilator Puritan Bennett', 'WORKING', 'ICU-Medical', ''),
            ('DEFIB-001', 'Defibrillator Zoll', 'MAINTENANCE', 'ER Room 3', 'Needs calibration'),
        ]
        for biomed, name, status, loc, remarks in equip_data:
            if not Equipment.query.filter_by(biomed=biomed).first():
                db.session.add(Equipment(biomed=biomed, name=name, status=status, location=loc, remarks=remarks))
        db.session.commit()

    def setUp(self):
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    # ── Helpers ──
    def _login(self, eid='ADMIN', pw='password123'):
        return self.client.post('/login', data={
            'employee_id': eid, 'password': pw
        }, follow_redirects=True)

    def _login_staff(self):
        return self._login('N001', 'password123')

    def _login_admin(self):
        return self._login('ADMIN', 'password123')

    # ═══════════════════════════════════════════════
    # SECTION 1: AUTH
    # ═══════════════════════════════════════════════
    def test_01_login_page_loads(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Sign In', r.data)

    def test_02_login_success_admin(self):
        r = self._login_admin()
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Logout', r.data)

    def test_03_login_success_staff(self):
        r = self._login_staff()
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Logout', r.data)

    def test_04_login_fail_wrong_password(self):
        r = self.client.post('/login', data={
            'employee_id': 'ADMIN', 'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Invalid', r.data)

    def test_05_login_fail_unapproved(self):
        r = self.client.post('/login', data={
            'employee_id': 'N002', 'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'pending', r.data)

    def test_06_logout(self):
        self._login_admin()
        r = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Sign In', r.data)

    def test_07_register_page_loads(self):
        r = self.client.get('/register')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Register', r.data)

    def test_08_register_new_staff(self):
        r = self.client.post('/register', data={
            'employee_id': 'TEST001',
            'full_name': 'Test Staff',
            'department': 'ER',
            'position': 'Nurse',
            'password': 'testpass123',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'approval', r.data)

    def test_09_register_duplicate_fails(self):
        r = self.client.post('/register', data={
            'employee_id': 'ADMIN',
            'full_name': 'Duplicate',
            'department': 'ER',
            'position': 'Nurse',
            'password': 'testpass123',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'already exists', r.data)

    def test_10_register_short_password_fails(self):
        r = self.client.post('/register', data={
            'employee_id': 'SHORT01',
            'full_name': 'Short Password',
            'department': 'ER',
            'position': 'Nurse',
            'password': 'short',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'8 characters', r.data)

    def test_11_session_redirects_to_login(self):
        self.client.get('/logout', follow_redirects=True)
        r = self.client.get('/', follow_redirects=True)
        self.assertIn(b'Sign In', r.data)

    def test_12_change_password(self):
        self._login_staff()
        r = self.client.post('/account/change-password', data={
            'old_password': 'password123',
            'new_password': 'newpass1234',
            'confirm_password': 'newpass1234',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        # Verify new password works
        self.client.get('/logout', follow_redirects=True)
        r = self.client.post('/login', data={
            'employee_id': 'N001', 'password': 'newpass1234'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'PULSE Dashboard', r.data)

        # Restore password
        self.client.post('/account/change-password', data={
            'old_password': 'newpass1234',
            'new_password': 'password123',
            'confirm_password': 'password123',
        }, follow_redirects=True)

    # ═══════════════════════════════════════════════
    # SECTION 2: SUPPLY MODULE
    # ═══════════════════════════════════════════════
    def test_20_dashboard_page(self):
        self._login_admin()
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'PULSE Dashboard', r.data)

    def test_21_dashboard_api(self):
        self._login_admin()
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('total_items', data)
        self.assertIn('shortage_count', data)
        self.assertIn('shortage_by_week', data)
        self.assertIn('critical_items', data)

    def test_22_dashboard_api_with_filter(self):
        self._login_admin()
        r = self.client.get('/api/dashboard?month=1&year=2024')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('total_items', data)

    def test_23_items_page(self):
        self._login_admin()
        r = self.client.get('/items')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Items', r.data)

    def test_24_add_item(self):
        self._login_admin()
        store = pulse_app.Store.query.first()
        r = self.client.post('/items/add', data={
            'code': 'TEST-ITEM-001',
            'name': 'Test Item',
            'store_id': str(store.id),
            'stock_quantity': '100',
            'critical_level': '10',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'added', r.data.lower())

    def test_25_edit_item(self):
        self._login_admin()
        item = pulse_app.Item.query.filter_by(code='PARA-001').first()
        self.assertIsNotNone(item)
        r = self.client.post(f'/items/{item.id}/edit', data={
            'name': 'Paracetamol 500mg (Updated)',
            'store_id': str(item.store_id),
            'stock_quantity': '600',
            'critical_level': '150',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_26_delete_item(self):
        self._login_admin()
        item = pulse_app.Item(
            code='DEL-ITEM', name='Delete Me',
            store_id=pulse_app.Store.query.first().id
        )
        db.session.add(item)
        db.session.commit()
        r = self.client.post(f'/items/{item.id}/delete', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(pulse_app.Item.query.filter_by(id=item.id).first())

    def test_27_report_new_page(self):
        self._login_admin()
        r = self.client.get('/report/new')
        self.assertEqual(r.status_code, 200)

    def test_28_submit_report(self):
        self._login_admin()
        item = pulse_app.Item.query.filter_by(code='PARA-001').first()
        week = pulse_app.Week.query.first()
        unit = pulse_app.Unit.query.first()
        ward = pulse_app.Ward.query.first()
        section = pulse_app.Section.query.first()
        r = self.client.post('/report/submit', data={
            'item_id': str(item.id),
            'week_id': str(week.id),
            'unit_id': str(unit.id),
            'ward_id': str(ward.id),
            'section_id': str(section.id),
            'status': 'Shortage',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_29_quick_report(self):
        self._login_admin()
        item = pulse_app.Item.query.filter_by(code='GLOV-001').first()
        r = self.client.post('/api/report/quick', data={
            'item_id': str(item.id),
        }, follow_redirects=True)
        self.assertIn(r.status_code, [200, 302])

    def test_30_reports_page(self):
        self._login_admin()
        r = self.client.get('/reports')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Reports', r.data)

    def test_31_shortage_export(self):
        self._login_admin()
        r = self.client.get('/export/shortage')
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      r.content_type)

    def test_32_una_export(self):
        self._login_admin()
        r = self.client.get('/export/una')
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      r.content_type)

    def test_33_reports_export(self):
        self._login_admin()
        r = self.client.get('/export/reports')
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      r.content_type)

    def test_34_import_items_xlsx(self):
        self._login_admin()
        wb = self._make_items_xlsx()
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = self.client.post('/items/import', data={
            'file': (buf, 'test_items.xlsx'),
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def _make_items_xlsx(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'Master List2'
        ws.append(['Code', 'Item', 'Store', 'Stock Quantity', 'Critical Level'])
        ws.append(['XLSX-001', 'Imported Item', 'Main Pharmacy', 50, 10])
        return wb

    # ═══════════════════════════════════════════════
    # SECTION 3: EQUIPMENT MODULE
    # ═══════════════════════════════════════════════
    def test_40_equipment_dashboard(self):
        self._login_admin()
        r = self.client.get('/equipment/dashboard')
        self.assertEqual(r.status_code, 200)

    def test_41_equipment_list(self):
        self._login_admin()
        r = self.client.get('/equipment/list')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Equipment', r.data)

    def test_42_add_equipment(self):
        self._login_admin()
        r = self.client.post('/equipment/add', data={
            'biomed': 'TEST-EQ-001',
            'name': 'Test Equipment',
            'status': 'WORKING',
            'location': 'Test Room',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_43_edit_equipment(self):
        self._login_admin()
        eq = pulse_app.Equipment.query.filter_by(biomed='BP-001').first()
        self.assertIsNotNone(eq)
        r = self.client.post(f'/equipment/{eq.id}/edit', data={
            'name': 'BP Apparatus (Updated)',
            'status': 'MAINTENANCE',
            'location': 'ICU-Medical',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_44_delete_equipment(self):
        self._login_admin()
        eq = pulse_app.Equipment(biomed='DEL-EQ', name='Delete Eq', status='WORKING')
        db.session.add(eq)
        db.session.commit()
        r = self.client.post(f'/equipment/{eq.id}/delete', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(pulse_app.Equipment.query.filter_by(id=eq.id).first())

    def test_45_equipment_detail(self):
        self._login_admin()
        eq = pulse_app.Equipment.query.filter_by(biomed='VENT-001').first()
        self.assertIsNotNone(eq)
        r = self.client.get(f'/equipment/{eq.id}')
        self.assertEqual(r.status_code, 200)

    def test_46_checkout_checkin(self):
        self._login_admin()
        eq = pulse_app.Equipment.query.filter_by(biomed='BP-001').first()
        self.assertIsNotNone(eq)
        # Checkout
        r = self.client.post(f'/equipment/{eq.id}/checkout', data={
            'checked_out_by': 'Dr. Smith',
            'destination': 'ER Triage',
            'purpose': 'Patient monitoring',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        # Check-in
        r = self.client.post(f'/equipment/{eq.id}/checkin', data={
            'checked_in_by': 'Dr. Smith',
            'condition': 'Good',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_47_scan_page(self):
        self._login_admin()
        r = self.client.get('/equipment/scan')
        self.assertEqual(r.status_code, 200)

    def test_48_equipment_api(self):
        self._login_admin()
        r = self.client.get('/api/equipment')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIsInstance(data, list)

    def test_49_equipment_dashboard_api(self):
        self._login_admin()
        r = self.client.get('/api/equipment/dashboard')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('total', data)

    def test_50_equipment_export(self):
        self._login_admin()
        r = self.client.get('/equipment/export')
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      r.content_type)

    def test_51_equipment_tracking(self):
        self._login_admin()
        r = self.client.get('/equipment/tracking')
        self.assertEqual(r.status_code, 200)

    def test_52_equipment_import_xlsx(self):
        self._login_admin()
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(['Biomedical', 'Name', 'Status', 'Location', 'Remarks'])
        ws.append(['IMP-EQ-01', 'Imported Equip', 'WORKING', 'ER Room 1', ''])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = self.client.post('/equipment/import', data={
            'file': (buf, 'test_equip.xlsx'),
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_53_qr_page(self):
        self._login_admin()
        r = self.client.get('/equipment/qr')
        self.assertEqual(r.status_code, 200)

    # ═══════════════════════════════════════════════
    # SECTION 4: ADMIN MODULE
    # ═══════════════════════════════════════════════
    def test_60_staff_list(self):
        self._login_admin()
        r = self.client.get('/staff/list')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Staff', r.data)

    def test_61_add_staff(self):
        self._login_admin()
        r = self.client.post('/staff/add', data={
            'employee_id': 'NEW001',
            'full_name': 'New Staff',
            'department': 'ER',
            'position': 'Doctor',
            'password': 'staffpass123',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_62_approve_staff(self):
        self._login_admin()
        staff = pulse_app.Staff.query.filter_by(employee_id='N002').first()
        self.assertIsNotNone(staff)
        r = self.client.post(f'/staff/{staff.id}/approve', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        db.session.refresh(staff)
        self.assertTrue(staff.approved)

    def test_63_reject_staff(self):
        self._login_admin()
        # Create unapproved staff to reject
        s = pulse_app.Staff(employee_id='REJ001', full_name='Reject Me', department='ER', position='Nurse')
        s.set_password('password123')
        s.approved = False
        db.session.add(s)
        db.session.commit()
        r = self.client.post(f'/staff/{s.id}/reject', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(pulse_app.Staff.query.filter_by(id=s.id).first())

    def test_64_set_staff_password(self):
        self._login_admin()
        staff = pulse_app.Staff.query.filter_by(employee_id='TEST001').first()
        self.assertIsNotNone(staff)
        r = self.client.post('/staff/set-password', data={
            'staff_id': str(staff.id),
            'new_password': 'newadminpass1',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_65_activity_log_page(self):
        self._login_admin()
        r = self.client.get('/activity-log')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Activity', r.data)

    def test_66_activity_api(self):
        self._login_admin()
        r = self.client.get('/api/activity')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIsInstance(data, list)

    def test_67_settings_page(self):
        self._login_admin()
        r = self.client.get('/settings')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Settings', r.data)

    def test_68_backup_trigger(self):
        self._login_admin()
        r = self.client.get('/backup', follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_69_admin_required_blocks_staff(self):
        self._login_staff()
        r = self.client.get('/staff/list', follow_redirects=True)
        self.assertEqual(r.status_code, 403)

    # ═══════════════════════════════════════════════
    # SECTION 5: UI ASSETS
    # ═══════════════════════════════════════════════
    def test_80_css_served(self):
        r = self.client.get('/static/style.css')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/css', r.content_type)

    def test_81_js_served(self):
        r = self.client.get('/static/script.js')
        self.assertEqual(r.status_code, 200)
        self.assertIn('javascript', r.content_type)

    # ═══════════════════════════════════════════════
    # SECTION 6: SEARCH & WARD API
    # ═══════════════════════════════════════════════
    def test_90_search(self):
        self._login_admin()
        r = self.client.get('/search?q=Paracetamol')
        self.assertEqual(r.status_code, 200)

    def test_91_wards_api(self):
        self._login_admin()
        unit = pulse_app.Unit.query.first()
        r = self.client.get(f'/api/wards/{unit.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIsInstance(data, list)

    def test_92_staff_search_api(self):
        self._login_admin()
        r = self.client.get('/api/staff/search?q=N001')
        self.assertEqual(r.status_code, 200)

    def test_93_staff_validate_api(self):
        self._login_admin()
        r = self.client.post('/api/staff/validate', data={
            'employee_id': 'N001'
        })
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn('valid', data)


if __name__ == '__main__':
    result = unittest.main(verbosity=2, exit=False)
    # Cleanup temp dir
    import shutil
    try:
        shutil.rmtree(_test_tmp, ignore_errors=True)
    except Exception:
        pass
    sys.exit(0 if result.result.wasSuccessful() else 1)
