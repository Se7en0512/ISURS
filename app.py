import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract

app = Flask(__name__)
app.secret_key = os.urandom(24)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'supplypulse.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    items = db.relationship('Item', backref='store', lazy=True)


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    wards = db.relationship('Ward', backref='unit', lazy=True)


class Ward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(300), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)


class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False, unique=True)
    date_range = db.Column(db.String(200))


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    week_id = db.Column(db.Integer, db.ForeignKey('week.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='reports')
    week = db.relationship('Week', backref='reports')
    unit = db.relationship('Unit', backref='reports')
    ward = db.relationship('Ward', backref='reports')
    section = db.relationship('Section', backref='reports')


with app.app_context():
    db.create_all()


@app.context_processor
def inject_globals():
    return dict(
        stores=Store.query.order_by(Store.name).all(),
        units=Unit.query.order_by(Unit.name).all(),
        sections=Section.query.order_by(Section.name).all(),
        weeks=Week.query.order_by(Week.week_number).all(),
        wards=Ward.query.order_by(Ward.name).all(),
        current_year=datetime.now().year,
        now=datetime.now,
        search_q=request.args.get('q', '')
    )


@app.route('/')
def dashboard():
    total_items = Item.query.count()
    total_reports = Report.query.count()
    shortage_count = Report.query.filter_by(status='Shortage').count()
    una_count = Report.query.filter_by(status='Not available').count()

    recent_reports = Report.query.order_by(
        Report.created_at.desc()).limit(10).all()

    shortage_by_store = db.session.query(
        Store.name, func.count(Report.id)
    ).select_from(Report).join(Item).join(Store).filter(
        Report.status == 'Shortage'
    ).group_by(Store.name).all()

    una_by_store = db.session.query(
        Store.name, func.count(Report.id)
    ).select_from(Report).join(Item).join(Store).filter(
        Report.status == 'Not available'
    ).group_by(Store.name).all()

    shortage_by_week = db.session.query(
        Week.week_number, Week.date_range, func.count(Report.id)
    ).select_from(Report).join(Week).filter(
        Report.status == 'Shortage'
    ).group_by(Week.week_number, Week.date_range).order_by(Week.week_number).all()

    una_by_week = db.session.query(
        Week.week_number, Week.date_range, func.count(Report.id)
    ).select_from(Report).join(Week).filter(
        Report.status == 'Not available'
    ).group_by(Week.week_number, Week.date_range).order_by(Week.week_number).all()

    return render_template('index.html',
                           total_items=total_items,
                           total_reports=total_reports,
                           shortage_count=shortage_count,
                           una_count=una_count,
                           recent_reports=recent_reports,
                           shortage_by_store=shortage_by_store,
                           una_by_store=una_by_store,
                           shortage_by_week=shortage_by_week,
                           una_by_week=una_by_week)


@app.route('/items')
def items():
    all_items = Item.query.order_by(Item.code).all()
    stores = Store.query.order_by(Store.name).all()
    return render_template('items.html', items=all_items, stores=stores)


@app.route('/items/add', methods=['POST'])
def add_item():
    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    store_id = request.form.get('store_id')
    if code and name and store_id:
        item = Item(code=code, name=name, store_id=store_id)
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully', 'success')
    return redirect(url_for('items'))


@app.route('/items/<int:id>/edit', methods=['POST'])
def edit_item(id):
    item = db.session.get(Item, id)
    if item:
        item.code = request.form.get('code', item.code).strip()
        item.name = request.form.get('name', item.name).strip()
        item.store_id = int(request.form.get('store_id', item.store_id))
        db.session.commit()
        flash('Item updated', 'success')
    return redirect(url_for('items'))


@app.route('/items/<int:id>/delete', methods=['POST'])
def delete_item(id):
    item = db.session.get(Item, id)
    if item:
        Report.query.filter_by(item_id=id).delete()
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted', 'success')
    return redirect(url_for('items'))


@app.route('/items/import', methods=['POST'])
def import_items():
    import openpyxl
    file = request.files.get('file')
    if not file:
        flash('No file selected', 'danger')
        return redirect(url_for('items'))
    wb = openpyxl.load_workbook(file)
    ws = wb['Master List2'] if 'Master List2' in wb.sheetnames else wb.active

    code_idx = None
    name_idx = None
    store_idx = None
    data_start = 1
    for row in ws.iter_rows(min_row=1, max_row=5, max_col=ws.min_column + 20, values_only=True):
        vals = [str(v).strip().lower() if v else '' for v in row]
        if 'code' in vals:
            code_idx = vals.index('code')
            name_idx = vals.index('item') if 'item' in vals else None
            store_idx = vals.index('store') if 'store' in vals else None
            data_start = data_start + 1
            break
        data_start += 1
    if code_idx is None:
        try:
            first = next(ws.iter_rows(min_row=data_start, max_row=data_start, max_col=data_start + 10, values_only=True))
            idx0 = str(first[0]).strip() if first[0] is not None else ''
        except:
            idx0 = ''
        if idx0.isdigit() and data_start > 1:
            code_idx, name_idx, store_idx = 1, 2, 3
        else:
            code_idx, name_idx, store_idx = 0, 1, 2

    need = [i for i in (code_idx, name_idx, store_idx) if i is not None]
    max_data_col = max(need) + 1 + ws.min_column

    count = 0
    for row in ws.iter_rows(min_row=data_start, min_col=ws.min_column, max_col=max_data_col, values_only=True):
        vals = [str(v).strip() if v is not None else '' for v in row]
        if len(vals) <= max(need):
            continue
        code = vals[code_idx]
        name = vals[name_idx] if name_idx is not None and len(vals) > name_idx else ''
        store_name = vals[store_idx] if store_idx is not None and len(vals) > store_idx else ''
        if not code or not name or not store_name:
            continue
        store = Store.query.filter_by(name=store_name).first()
        if not store:
            store = Store(name=store_name)
            db.session.add(store)
            db.session.commit()
        if not Item.query.filter_by(code=code).first():
            item = Item(code=code, name=name, store_id=store.id)
            db.session.add(item)
            count += 1
    db.session.commit()
    flash(f'{count} items imported', 'success')
    return redirect(url_for('items'))


@app.route('/report/new')
def report_new():
    items = Item.query.order_by(Item.code).all()
    weeks = Week.query.order_by(Week.week_number).all()
    units = Unit.query.order_by(Unit.name).all()
    sections = Section.query.order_by(Section.name).all()
    return render_template('report_new.html', items=items, weeks=weeks,
                           units=units, sections=sections)


@app.route('/api/wards/<int:unit_id>')
def api_wards(unit_id):
    wards = Ward.query.filter_by(unit_id=unit_id).order_by(Ward.name).all()
    return jsonify([{'id': w.id, 'name': w.name} for w in wards])


@app.route('/report/submit', methods=['POST'])
def report_submit():
    item_id = request.form.get('item_id')
    week_id = request.form.get('week_id')
    unit_id = request.form.get('unit_id')
    ward_id = request.form.get('ward_id')
    section_id = request.form.get('section_id')
    status = request.form.get('status')
    if all([item_id, week_id, unit_id, ward_id, section_id, status]):
        report = Report(
            item_id=item_id, week_id=week_id, unit_id=unit_id,
            ward_id=ward_id, section_id=section_id, status=status
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted', 'success')
    else:
        flash('All fields required', 'danger')
    return redirect(url_for('reports'))


@app.route('/report/import', methods=['POST'])
def import_reports():
    import openpyxl
    from datetime import datetime
    file = request.files.get('file')
    if not file:
        flash('No file selected', 'danger')
        return redirect(url_for('reports'))
    try:
        wb = openpyxl.load_workbook(file)
        ws = wb['Report'] if 'Report' in wb.sheetnames else wb.active

        header = None
        header_row = 0
        for row in ws.iter_rows(min_row=1, max_row=5, max_col=ws.min_column + 20, values_only=True):
            header_row += 1
            vals = [str(v).strip().lower() if v else '' for v in row]
            if 'code' in vals:
                header = vals
                break
        if not header:
            flash('Could not find header row with "Code" column in Report sheet', 'danger')
            return redirect(url_for('reports'))
        try:
            code_idx = header.index('code')
            status_idx = header.index('status')
        except ValueError as e:
            flash(f'Missing required column in Report sheet: {e}', 'danger')
            return redirect(url_for('reports'))
        name_idx = header.index('item') if 'item' in header else None
        store_idx = header.index('store') if 'store' in header else None
        week_idx = header.index('week') if 'week' in header else None
        unit_idx = header.index('unit') if 'unit' in header else None
        ward_idx = header.index('ward') if 'ward' in header else None
        section_idx = header.index('section') if 'section' in header else None

        need = [i for i in (code_idx, status_idx, name_idx, store_idx, week_idx, unit_idx, ward_idx, section_idx) if i is not None]
        max_data_col = max(need) + 1 + ws.min_column

        count = 0
        errors = []
        for i, row in enumerate(ws.iter_rows(min_row=header_row + 1, min_col=ws.min_column, max_col=max_data_col, values_only=True), start=header_row + 1):
            vals = [str(v).strip() if v is not None else '' for v in row]
            if len(vals) <= max(code_idx, status_idx):
                continue
            code = vals[code_idx]
            status_raw = vals[status_idx]
            if not code or not status_raw:
                continue
            section_name = vals[section_idx] if section_idx is not None and len(vals) > section_idx else ''
            unit_name = vals[unit_idx] if unit_idx is not None and len(vals) > unit_idx else ''
            ward_name = vals[ward_idx] if ward_idx is not None and len(vals) > ward_idx else ''
            item_name = vals[name_idx] if name_idx is not None and len(vals) > name_idx else ''
            store_name = vals[store_idx] if store_idx is not None and len(vals) > store_idx else ''
            week_raw = vals[week_idx] if week_idx is not None and len(vals) > week_idx else ''
            item = Item.query.filter_by(code=code).first()
            if not item:
                errors.append(f'Row {i}: Item code "{code}" not found')
                continue
            import re
            nums = re.findall(r'\d+', str(week_raw))
            week_num = int(nums[0]) if nums else None
            week = Week.query.filter_by(week_number=week_num).first() if week_num else None
            if not week and week_num:
                week = Week(week_number=week_num, date_range=str(week_raw))
                db.session.add(week)
                db.session.commit()
            if not week:
                errors.append(f'Row {i}: Week not found (value: {week_raw})')
                continue
            unit = Unit.query.filter_by(name=unit_name).first() if unit_name else None
            ward = Ward.query.filter_by(name=ward_name).first() if ward_name else None
            section = Section.query.filter_by(name=section_name).first() if section_name else None
            if not unit:
                unit = Unit(name=unit_name) if unit_name else None
                if unit:
                    db.session.add(unit)
                    db.session.commit()
            if not ward and unit and ward_name:
                ward = Ward(name=ward_name, unit_id=unit.id)
                db.session.add(ward)
                db.session.commit()
            if not section and section_name:
                section = Section(name=section_name)
                db.session.add(section)
                db.session.commit()
            s = 'Shortage' if status_raw.lower() == 'shortage' else 'Not available'
            report = Report(
                item_id=item.id, week_id=week.id,
                unit_id=unit.id if unit else 1,
                ward_id=ward.id if ward else 1,
                section_id=section.id if section else 1,
                status=s
            )
            db.session.add(report)
            count += 1
        db.session.commit()
        msg = f'{count} reports imported'
        if errors:
            msg += f'. Errors: {"; ".join(errors[:5])}'
        flash(msg, 'success' if count else 'danger')
    except Exception as e:
        flash(f'Import failed: {e}', 'danger')
    return redirect(url_for('reports'))


@app.route('/reports')
def reports():
    page = request.args.get('page', 1, type=int)
    store_id = request.args.get('store_id', type=int)
    status_filter = request.args.get('status')
    week_id = request.args.get('week_id', type=int)

    query = Report.query
    if store_id:
        query = query.join(Item).filter(Item.store_id == store_id)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    if week_id:
        query = query.filter(Report.week_id == week_id)

    query = query.order_by(Report.created_at.desc())
    pagination = query.paginate(page=page, per_page=50)
    return render_template('reports.html', pagination=pagination,
                           stores=Store.query.order_by(Store.name).all())


@app.route('/shortage')
def shortage():
    store_id = request.args.get('store_id', type=int)

    query = db.session.query(
        Item.code, Item.name, Store.name.label('store'),
        func.count(Report.id).label('total')
    ).select_from(Report).join(Item).join(Store).filter(
        Report.status == 'Shortage'
    )
    if store_id:
        query = query.filter(Item.store_id == store_id)
    data = query.group_by(Item.id, Item.code, Item.name, Store.name)\
                .order_by(func.count(Report.id).desc()).all()

    return render_template('shortage.html', data=data)


@app.route('/una')
def una():
    store_id = request.args.get('store_id', type=int)

    query = db.session.query(
        Item.code, Item.name, Store.name.label('store'),
        func.count(Report.id).label('total')
    ).select_from(Report).join(Item).join(Store).filter(
        Report.status == 'Not available'
    )
    if store_id:
        query = query.filter(Item.store_id == store_id)
    data = query.group_by(Item.id, Item.code, Item.name, Store.name)\
                .order_by(func.count(Report.id).desc()).all()

    return render_template('una.html', data=data)


@app.route('/settings')
def settings():
    stores = Store.query.order_by(Store.name).all()
    units = Unit.query.order_by(Unit.name).all()
    wards = Ward.query.order_by(Ward.name).all()
    sections = Section.query.order_by(Section.name).all()
    weeks = Week.query.order_by(Week.week_number).all()
    return render_template('settings.html', stores=stores, units=units,
                           wards=wards, sections=sections, weeks=weeks)


@app.route('/settings/store/add', methods=['POST'])
def add_store():
    name = request.form.get('name', '').strip()
    if name and not Store.query.filter_by(name=name).first():
        db.session.add(Store(name=name))
        db.session.commit()
        flash('Store added', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/store/<int:id>/delete', methods=['POST'])
def delete_store(id):
    store = db.session.get(Store, id)
    if store:
        Item.query.filter_by(store_id=id).delete()
        db.session.delete(store)
        db.session.commit()
        flash('Store deleted', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/unit/add', methods=['POST'])
def add_unit():
    name = request.form.get('name', '').strip()
    if name and not Unit.query.filter_by(name=name).first():
        db.session.add(Unit(name=name))
        db.session.commit()
        flash('Unit added', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/ward/add', methods=['POST'])
def add_ward():
    name = request.form.get('name', '').strip()
    unit_id = request.form.get('unit_id')
    if name and unit_id:
        db.session.add(Ward(name=name, unit_id=unit_id))
        db.session.commit()
        flash('Ward added', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/section/add', methods=['POST'])
def add_section():
    name = request.form.get('name', '').strip()
    if name and not Section.query.filter_by(name=name).first():
        db.session.add(Section(name=name))
        db.session.commit()
        flash('Section added', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/week/add', methods=['POST'])
def add_week():
    week_number = request.form.get('week_number', type=int)
    date_range = request.form.get('date_range', '').strip()
    if week_number and not Week.query.filter_by(week_number=week_number).first():
        db.session.add(Week(week_number=week_number, date_range=date_range))
        db.session.commit()
        flash('Week added', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/seed', methods=['POST'])
def seed_from_excel():
    import openpyxl
    file = request.files.get('file')
    if not file:
        flash('No file selected', 'danger')
        return redirect(url_for('settings'))

    wb = openpyxl.load_workbook(file)

    if 'Droplist' in wb.sheetnames:
        ws = wb['Droplist']
        mc = ws.min_column
        if mc < 1:
            mc = 1

        for row in ws.iter_rows(min_row=2, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            date_raw = str(vals[0]).strip() if len(vals) > 0 and vals[0] else ''
            week_raw = vals[1] if len(vals) > 1 else None
            if isinstance(week_raw, (int, float)) and week_raw > 0:
                if not Week.query.filter_by(week_number=int(week_raw)).first():
                    db.session.add(Week(week_number=int(week_raw), date_range=date_raw))

        store_names = set()
        for row in ws.iter_rows(min_row=2, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            store_val = str(vals[3]).strip() if len(vals) > 3 and vals[3] else ''
            if store_val:
                store_names.add(store_val)
        for name in store_names:
            if not Store.query.filter_by(name=name).first():
                db.session.add(Store(name=name))

        rows_data = []
        for row in ws.iter_rows(min_row=5, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            u = str(vals[7]).strip() if len(vals) > 7 and vals[7] else ''
            w = str(vals[8]).strip() if len(vals) > 8 and vals[8] else ''
            s = str(vals[9]).strip() if len(vals) > 9 and vals[9] else ''
            if u or s:
                rows_data.append((u, w, s))

        seen_units = set()
        for u, w, s in rows_data:
            if u and u not in seen_units:
                seen_units.add(u)
                if not Unit.query.filter_by(name=u).first():
                    db.session.add(Unit(name=u))
            if s and not Section.query.filter_by(name=s).first():
                db.session.add(Section(name=s))

        db.session.commit()

        for u, w, s in rows_data:
            if u and w:
                unit = Unit.query.filter_by(name=u).first()
                if unit and not Ward.query.filter_by(name=w, unit_id=unit.id).first():
                    db.session.add(Ward(name=w, unit_id=unit.id))

        db.session.commit()

    flash('Reference data seeded from Excel', 'success')
    return redirect(url_for('settings'))


@app.route('/import-all', methods=['POST'])
def import_all():
    import openpyxl
    file = request.files.get('file')
    if not file:
        flash('No file selected', 'danger')
        return redirect(request.referrer or url_for('dashboard'))

    wb = openpyxl.load_workbook(file)
    results = []

    def _find_header(ws, keywords):
        for row in ws.iter_rows(min_row=1, max_row=10, max_col=ws.min_column + 20, values_only=True):
            vals = [str(v).strip().lower() if v else '' for v in row]
            if all(k in vals for k in keywords):
                return vals, [vals.index(k) for k in keywords]
        return None, None

    if 'Droplist' in wb.sheetnames:
        ws = wb['Droplist']
        mc = ws.min_column
        if mc < 1:
            mc = 1
        week_count = 0
        for row in ws.iter_rows(min_row=2, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            date_raw = str(vals[0]).strip() if len(vals) > 0 and vals[0] else ''
            week_raw = vals[1] if len(vals) > 1 else None
            if isinstance(week_raw, (int, float)) and week_raw > 0:
                if not Week.query.filter_by(week_number=int(week_raw)).first():
                    db.session.add(Week(week_number=int(week_raw), date_range=date_raw))
                    week_count += 1
        store_names = set()
        for row in ws.iter_rows(min_row=2, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            store_val = str(vals[3]).strip() if len(vals) > 3 and vals[3] else ''
            if store_val:
                store_names.add(store_val)
        for name in store_names:
            if not Store.query.filter_by(name=name).first():
                db.session.add(Store(name=name))
        rows_data = []
        for row in ws.iter_rows(min_row=5, min_col=mc, max_col=mc + 15, values_only=True):
            vals = list(row)
            u = str(vals[7]).strip() if len(vals) > 7 and vals[7] else ''
            w = str(vals[8]).strip() if len(vals) > 8 and vals[8] else ''
            s = str(vals[9]).strip() if len(vals) > 9 and vals[9] else ''
            if u or s:
                rows_data.append((u, w, s))
        seen_units = set()
        for u, w, s in rows_data:
            if u and u not in seen_units:
                seen_units.add(u)
                if not Unit.query.filter_by(name=u).first():
                    db.session.add(Unit(name=u))
            if s and not Section.query.filter_by(name=s).first():
                db.session.add(Section(name=s))
        db.session.commit()
        for u, w, s in rows_data:
            if u and w:
                unit = Unit.query.filter_by(name=u).first()
                if unit and not Ward.query.filter_by(name=w, unit_id=unit.id).first():
                    db.session.add(Ward(name=w, unit_id=unit.id))
        db.session.commit()
        results.append(f'{week_count} weeks, {len(store_names)} stores, {len(set(r[0] for r in rows_data if r[0]))} units, {len(set(r[2] for r in rows_data if r[2]))} sections seeded')

    if 'Master List2' in wb.sheetnames:
        ws = wb['Master List2']
        header, idxs = _find_header(ws, ['code'])
        if header:
            code_idx = idxs[0]
            name_idx = header.index('item') if 'item' in header else code_idx + 1
            store_idx = header.index('store') if 'store' in header else code_idx + 2
            need = [i for i in (code_idx, name_idx, store_idx) if i is not None]
            max_col = max(need) + 1 + ws.min_column
            item_count = 0
            for row in ws.iter_rows(min_row=5, min_col=ws.min_column, max_col=max_col, values_only=True):
                vals = [str(v).strip() if v is not None else '' for v in row]
                if len(vals) <= max(need):
                    continue
                code = vals[code_idx]
                name = vals[name_idx] if name_idx is not None and len(vals) > name_idx else ''
                store_name = vals[store_idx] if store_idx is not None and len(vals) > store_idx else ''
                if not code or not name or not store_name:
                    continue
                store = Store.query.filter_by(name=store_name).first()
                if not store:
                    store = Store(name=store_name)
                    db.session.add(store)
                    db.session.commit()
                if not Item.query.filter_by(code=code).first():
                    db.session.add(Item(code=code, name=name, store_id=store.id))
                    item_count += 1
            db.session.commit()
            results.append(f'{item_count} items imported')
        else:
            results.append('Master List2: header not found')

    if 'Report' in wb.sheetnames:
        ws = wb['Report']
        header, idxs = _find_header(ws, ['code', 'status'])
        if header:
            code_idx = idxs[0]
            status_idx = idxs[1]
            name_idx = header.index('item') if 'item' in header else None
            store_idx = header.index('store') if 'store' in header else None
            week_idx = header.index('week') if 'week' in header else None
            unit_idx = header.index('unit') if 'unit' in header else None
            ward_idx = header.index('ward') if 'ward' in header else None
            section_idx = header.index('section') if 'section' in header else None
            need = [i for i in (code_idx, status_idx) if i is not None]
            max_col = max(need) + 1 + ws.min_column
            import re
            report_count = 0
            errors = []
            for i, row in enumerate(ws.iter_rows(min_row=3, min_col=ws.min_column, max_col=max_col, values_only=True), start=3):
                vals = [str(v).strip() if v is not None else '' for v in row]
                if len(vals) <= max(need):
                    continue
                code = vals[code_idx]
                status_raw = vals[status_idx]
                if not code or not status_raw:
                    continue
                section_name = vals[section_idx] if section_idx is not None and len(vals) > section_idx else ''
                unit_name = vals[unit_idx] if unit_idx is not None and len(vals) > unit_idx else ''
                ward_name = vals[ward_idx] if ward_idx is not None and len(vals) > ward_idx else ''
                item_name = vals[name_idx] if name_idx is not None and len(vals) > name_idx else ''
                store_name = vals[store_idx] if store_idx is not None and len(vals) > store_idx else ''
                week_raw = vals[week_idx] if week_idx is not None and len(vals) > week_idx else ''
                item = Item.query.filter_by(code=code).first()
                if not item:
                    errors.append(f'Row {i}: Item code "{code}" not found')
                    continue
                nums = re.findall(r'\d+', str(week_raw))
                week_num = int(nums[0]) if nums else None
                week = Week.query.filter_by(week_number=week_num).first() if week_num else None
                if not week and week_num:
                    week = Week(week_number=week_num, date_range=str(week_raw))
                    db.session.add(week)
                    db.session.commit()
                if not week:
                    errors.append(f'Row {i}: Week not found ({week_raw})')
                    continue
                unit = Unit.query.filter_by(name=unit_name).first() if unit_name else None
                ward = Ward.query.filter_by(name=ward_name).first() if ward_name else None
                section = Section.query.filter_by(name=section_name).first() if section_name else None
                if not unit and unit_name:
                    unit = Unit(name=unit_name)
                    db.session.add(unit)
                    db.session.commit()
                if not ward and unit and ward_name:
                    ward = Ward(name=ward_name, unit_id=unit.id)
                    db.session.add(ward)
                    db.session.commit()
                if not section and section_name:
                    section = Section(name=section_name)
                    db.session.add(section)
                    db.session.commit()
                s = 'Shortage' if status_raw.lower() == 'shortage' else 'Not available'
                if not Report.query.filter_by(item_id=item.id, week_id=week.id, status=s).first():
                    db.session.add(Report(
                        item_id=item.id, week_id=week.id,
                        unit_id=unit.id if unit else 1,
                        ward_id=ward.id if ward else 1,
                        section_id=section.id if section else 1,
                        status=s
                    ))
                    report_count += 1
            db.session.commit()
            msg = f'{report_count} reports imported'
            if errors:
                msg += f' ({len(errors)} errors: {errors[0]}{"..." if len(errors)>1 else ""})'
            results.append(msg)
        else:
            results.append('Report: header not found')

    flash('Import complete: ' + ' | '.join(results), 'success')
    return redirect(url_for('dashboard'))


@app.route('/settings/clear', methods=['POST'])
def clear_data():
    Report.query.delete()
    Item.query.delete()
    Store.query.delete()
    Week.query.delete()
    Unit.query.delete()
    Ward.query.delete()
    Section.query.delete()
    db.session.commit()
    flash('All data cleared', 'success')
    return redirect(url_for('settings'))


@app.route('/export/reports')
def export_reports():
    import openpyxl
    from io import BytesIO
    from flask import send_file

    store_id = request.args.get('store_id', type=int)
    status_filter = request.args.get('status')
    week_id = request.args.get('week_id', type=int)

    query = Report.query
    if store_id:
        query = query.join(Item).filter(Item.store_id == store_id)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    if week_id:
        query = query.filter(Report.week_id == week_id)
    query = query.order_by(Report.created_at.desc())
    reports = query.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Reports'
    ws.append(['Item Code', 'Item Name', 'Store', 'Week', 'Unit', 'Ward', 'Section', 'Status', 'Reported'])
    for r in reports:
        ws.append([r.item.code, r.item.name, r.item.store.name, f'Week {r.week.week_number}',
                   r.unit.name, r.ward.name, r.section.name, r.status,
                   r.created_at.strftime('%Y-%m-%d')])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='ISURS_reports.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/export/shortage')
def export_shortage():
    import openpyxl
    from io import BytesIO
    from flask import send_file

    store_id = request.args.get('store_id', type=int)
    query = db.session.query(Item.code, Item.name, Store.name.label('store'),
                             func.count(Report.id).label('total')
                             ).select_from(Report).join(Item).join(Store).filter(Report.status == 'Shortage')
    if store_id:
        query = query.filter(Item.store_id == store_id)
    data = query.group_by(Item.id, Item.code, Item.name, Store.name).order_by(func.count(Report.id).desc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Shortage'
    ws.append(['Code', 'Item', 'Store', 'Times Reported'])
    for code, name, store, total in data:
        ws.append([code, name, store, total])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='ISURS_shortage.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/export/una')
def export_una():
    import openpyxl
    from io import BytesIO
    from flask import send_file

    store_id = request.args.get('store_id', type=int)
    query = db.session.query(Item.code, Item.name, Store.name.label('store'),
                             func.count(Report.id).label('total')
                             ).select_from(Report).join(Item).join(Store).filter(Report.status == 'Not available')
    if store_id:
        query = query.filter(Item.store_id == store_id)
    data = query.group_by(Item.id, Item.code, Item.name, Store.name).order_by(func.count(Report.id).desc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Not Available'
    ws.append(['Code', 'Item', 'Store', 'Times Reported'])
    for code, name, store, total in data:
        ws.append([code, name, store, total])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='ISURS_una.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/download/readme')
def download_readme():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'README.md',
                               as_attachment=True, download_name='ISURS_README.md')


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    items = []
    reports = []
    if q:
        items = Item.query.filter(
            Item.code.ilike(f'%{q}%') | Item.name.ilike(f'%{q}%')
        ).order_by(Item.code).limit(30).all()
        reports = Report.query.join(Item).filter(
            Item.code.ilike(f'%{q}%') | Item.name.ilike(f'%{q}%')
        ).order_by(Report.created_at.desc()).limit(30).all()
    return render_template('search.html', q=q, items=items, reports=reports)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
