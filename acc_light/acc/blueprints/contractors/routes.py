from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.contractors import bp
from acc.models import Contractor, Voucher, Project
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination
from sqlalchemy import func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Base query
    query = Contractor.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Contractor.name.ilike(f'%{search}%'),
                Contractor.phone.ilike(f'%{search}%'),
                Contractor.specialization.ilike(f'%{search}%')
            )
        )
    
    # Order by name
    query = query.order_by(Contractor.name)
    
    # Pagination
    pagination = Pagination(query, page)
    contractors = pagination.items
    
    # Calculate stats
    total_contractors = Contractor.query.count()
    
    # Calculate total payments to contractors
    total_payments = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.entity_type == 'contractor',
        Voucher.type == 'payment'
    ).scalar() or 0
    
    # Active projects count
    active_projects = Project.query.filter_by(status='جاري').count()
    
    return render_template('contractors/index.html',
                         contractors=contractors,
                         pagination=pagination,
                         search=search,
                         total_contractors=total_contractors,
                         total_payments=total_payments,
                         active_projects=active_projects)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        specialization = request.form.get('specialization', '').strip()
        address = request.form.get('address', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم المقاول', 'error')
            return redirect(url_for('contractors.add'))
        
        # Check duplicate
        if Contractor.query.filter_by(name=name).first():
            flash('اسم المقاول موجود بالفعل', 'error')
            return redirect(url_for('contractors.add'))
        
        contractor = Contractor(
            id=generate_uid('CN'),
            name=name,
            phone=phone,
            email=email,
            specialization=specialization,
            address=address,
            notes=notes
        )
        
        db.session.add(contractor)
        log_action('إضافة مقاول جديد', {'id': contractor.id, 'name': contractor.name})
        db.session.commit()
        
        flash('تم إضافة المقاول بنجاح', 'success')
        return redirect(url_for('contractors.detail', id=contractor.id))
    
    return render_template('contractors/add.html')


@bp.route('/<id>')
def detail(id):
    contractor = Contractor.query.get_or_404(id)
    
    # Get contractor projects
    projects = Project.query.filter_by(contractor_id=id).order_by(Project.start_date.desc()).all()
    
    # Get contractor vouchers
    vouchers = Voucher.query.filter_by(
        entity_type='contractor',
        entity_id=id
    ).order_by(Voucher.date.desc()).limit(10).all()
    
    # Calculate totals
    total_payments = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.entity_type == 'contractor',
        Voucher.entity_id == id,
        Voucher.type == 'payment'
    ).scalar() or 0
    
    total_receipts = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.entity_type == 'contractor',
        Voucher.entity_id == id,
        Voucher.type == 'receipt'
    ).scalar() or 0
    
    balance = total_receipts - total_payments
    
    # Projects stats
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status == 'جاري')
    
    return render_template('contractors/detail.html',
                         contractor=contractor,
                         projects=projects,
                         vouchers=vouchers,
                         total_payments=total_payments,
                         total_receipts=total_receipts,
                         balance=balance,
                         total_projects=total_projects,
                         active_projects=active_projects)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    contractor = Contractor.query.get_or_404(id)
    
    if request.method == 'POST':
        contractor.name = request.form.get('name', '').strip()
        contractor.phone = request.form.get('phone', '').strip()
        contractor.email = request.form.get('email', '').strip()
        contractor.specialization = request.form.get('specialization', '').strip()
        contractor.address = request.form.get('address', '').strip()
        contractor.notes = request.form.get('notes', '').strip()
        
        if not contractor.name:
            flash('الرجاء إدخال اسم المقاول', 'error')
            return redirect(url_for('contractors.edit', id=id))
        
        # Check duplicate
        existing = Contractor.query.filter_by(name=contractor.name).first()
        if existing and existing.id != id:
            flash('اسم المقاول موجود بالفعل', 'error')
            return redirect(url_for('contractors.edit', id=id))
        
        log_action('تعديل مقاول', {'id': contractor.id, 'name': contractor.name})
        db.session.commit()
        
        flash('تم تحديث بيانات المقاول بنجاح', 'success')
        return redirect(url_for('contractors.detail', id=id))
    
    return render_template('contractors/edit.html', contractor=contractor)


# API endpoints
@bp.route('/api/contractors')
def api_contractors():
    contractors = Contractor.query.order_by(Contractor.name).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'specialization': c.specialization
    } for c in contractors])