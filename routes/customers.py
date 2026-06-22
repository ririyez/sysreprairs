from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from models import Customer
from sqlalchemy import or_

bp = Blueprint('customers', __name__, url_prefix='/customers')

@bp.route('/')
@login_required
def index():
    """Daftar Pelanggan"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query
    if search:
        query = query.filter(or_(
            Customer.name.ilike(f'%{search}%'),
            Customer.phone.ilike(f'%{search}%'),
            Customer.email.ilike(f'%{search}%')
        ))
    
    customers = query.order_by(Customer.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('customers/index.html', customers=customers, search=search)

@bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    """Tambah Pelanggan Baru"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        province = request.form.get('province')
        postal_code = request.form.get('postal_code')
        notes = request.form.get('notes')
        
        if not name or not phone:
            flash('Nama dan nomor telepon harus diisi!', 'danger')
            return redirect(url_for('customers.tambah'))
        
        # Cek nomor telepon sudah ada
        if Customer.query.filter_by(phone=phone).first():
            flash('Nomor telepon sudah terdaftar!', 'danger')
            return redirect(url_for('customers.tambah'))
        
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            province=province,
            postal_code=postal_code,
            notes=notes
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Pelanggan berhasil ditambahkan!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit Pelanggan"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        province = request.form.get('province')
        postal_code = request.form.get('postal_code')
        notes = request.form.get('notes')
        
        if not name or not phone:
            flash('Nama dan nomor telepon harus diisi!', 'danger')
            return redirect(url_for('customers.edit', id=id))
        
        # Cek nomor telepon sudah ada (yang lain)
        existing = Customer.query.filter(Customer.phone == phone, Customer.id != id).first()
        if existing:
            flash('Nomor telepon sudah terdaftar!', 'danger')
            return redirect(url_for('customers.edit', id=id))
        
        customer.name = name
        customer.phone = phone
        customer.email = email
        customer.address = address
        customer.city = city
        customer.province = province
        customer.postal_code = postal_code
        customer.notes = notes
        
        db.session.commit()
        flash('Pelanggan berhasil diperbarui!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html', customer=customer)

@bp.route('/<int:id>/hapus', methods=['POST'])
@login_required
def hapus(id):
    """Hapus Pelanggan"""
    customer = Customer.query.get_or_404(id)
    
    # Cek apakah pelanggan memiliki order
    if customer.orders:
        flash('Tidak dapat menghapus pelanggan yang memiliki order!', 'danger')
        return redirect(url_for('customers.index'))
    
    db.session.delete(customer)
    db.session.commit()
    
    flash('Pelanggan berhasil dihapus!', 'success')
    return redirect(url_for('customers.index'))

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Detail Pelanggan"""
    customer = Customer.query.get_or_404(id)
    return render_template('customers/detail.html', customer=customer)
