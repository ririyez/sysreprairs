from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from models import Order, Customer, Service, Transaction
from datetime import datetime
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename
from PIL import Image

bp = Blueprint('orders', __name__, url_prefix='/orders')

def allowed_file(filename):
    """Cek file yang diperbolehkan"""
    from flask import current_app
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_upload_file(file, folder_name):
    """Simpan dan compress file upload"""
    if file and allowed_file(file.filename):
        from flask import current_app
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(filepath, exist_ok=True)
        
        full_path = os.path.join(filepath, filename)
        file.save(full_path)
        
        # Compress image
        try:
            img = Image.open(full_path)
            img.thumbnail((1200, 1200))
            img.save(full_path, quality=85, optimize=True)
        except:
            pass
        
        return os.path.join(folder_name, filename)
    return None

@bp.route('/')
@login_required
def index():
    """Daftar Order Reparasi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Order.query
    
    if search:
        query = query.join(Customer).filter(or_(
            Order.invoice_number.ilike(f'%{search}%'),
            Customer.name.ilike(f'%{search}%'),
            Customer.phone.ilike(f'%{search}%')
        ))
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    
    status_options = [
        ('diterima', 'Diterima'),
        ('proses', 'Sedang Diproses'),
        ('selesai', 'Selesai'),
        ('diambil', 'Sudah Diambil')
    ]
    
    return render_template('orders/index.html', 
                         orders=orders, 
                         search=search, 
                         status_filter=status_filter,
                         status_options=status_options)

def generate_invoice_number():
    """Generate nomor invoice otomatis"""
    from datetime import datetime
    date_str = datetime.utcnow().strftime('%Y%m%d')
    
    # Cari nomor invoice terakhir hari ini
    last_invoice = Order.query.filter(
        Order.invoice_number.ilike(f'{date_str}%')
    ).order_by(Order.invoice_number.desc()).first()
    
    if last_invoice:
        # Extract nomor urut
        last_number = int(last_invoice.invoice_number[-4:])
        next_number = last_number + 1
    else:
        next_number = 1
    
    invoice_number = f'{date_str}{next_number:04d}'
    return invoice_number

@bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    """Tambah Order Baru"""
    services = Service.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')
        shoe_type = request.form.get('shoe_type')
        shoe_brand = request.form.get('shoe_brand')
        shoe_color = request.form.get('shoe_color')
        complaint = request.form.get('complaint')
        price = request.form.get('price')
        discount = request.form.get('discount', 0)
        
        if not all([customer_id, service_id, shoe_type, shoe_brand, shoe_color, complaint, price]):
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('orders.tambah'))
        
        try:
            price = float(price)
            discount = float(discount) if discount else 0
            
            if price < 0 or discount < 0:
                raise ValueError('Harga tidak boleh negatif')
            
            total_price = price - discount
            
            if total_price <= 0:
                raise ValueError('Total harga harus lebih dari 0')
            
        except ValueError as e:
            flash(f'Harga tidak valid: {str(e)}', 'danger')
            return redirect(url_for('orders.tambah'))
        
        invoice_number = generate_invoice_number()
        
        order = Order(
            invoice_number=invoice_number,
            customer_id=int(customer_id),
            service_id=int(service_id),
            shoe_type=shoe_type,
            shoe_brand=shoe_brand,
            shoe_color=shoe_color,
            complaint=complaint,
            price=price,
            discount=discount,
            total_price=total_price
        )
        
        # Upload foto sebelum
        before_photo = request.files.get('before_photo')
        if before_photo:
            filename = save_upload_file(before_photo, 'sebelum')
            if filename:
                order.before_photo = filename
        
        db.session.add(order)
        db.session.flush()
        
        # Buat transaksi (order baru)
        transaction = Transaction(
            order_id=order.id,
            transaction_type='income',
            description=f'Order {invoice_number} - {Customer.query.get(customer_id).name}',
            amount=total_price,
            payment_method='belum_bayar',
            reference_number=invoice_number
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Order berhasil ditambahkan dengan nomor invoice: {invoice_number}', 'success')
        return redirect(url_for('orders.detail', id=order.id))
    
    shoe_types = ['Casual', 'Formal', 'Olahraga', 'Sneaker', 'Boot', 'Sepatu Kerja', 'Lainnya']
    
    return render_template('orders/form.html', 
                         services=services, 
                         customers=customers,
                         shoe_types=shoe_types)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit Order"""
    order = Order.query.get_or_404(id)
    services = Service.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        shoe_type = request.form.get('shoe_type')
        shoe_brand = request.form.get('shoe_brand')
        shoe_color = request.form.get('shoe_color')
        complaint = request.form.get('complaint')
        status = request.form.get('status')
        progress_percentage = request.form.get('progress_percentage', 0)
        notes = request.form.get('notes')
        
        if not all([shoe_type, shoe_brand, shoe_color, complaint]):
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('orders.edit', id=id))
        
        try:
            progress_percentage = int(progress_percentage)
            if not (0 <= progress_percentage <= 100):
                raise ValueError('Progress harus 0-100')
        except ValueError:
            flash('Progress tidak valid!', 'danger')
            return redirect(url_for('orders.edit', id=id))
        
        order.shoe_type = shoe_type
        order.shoe_brand = shoe_brand
        order.shoe_color = shoe_color
        order.complaint = complaint
        order.status = status
        order.progress_percentage = progress_percentage
        order.notes = notes
        
        # Update completed_date jika status selesai
        if status == 'selesai' and not order.completed_date:
            order.completed_date = datetime.utcnow()
        
        # Upload foto sesudah
        after_photo = request.files.get('after_photo')
        if after_photo:
            filename = save_upload_file(after_photo, 'sesudah')
            if filename:
                order.after_photo = filename
        
        db.session.commit()
        flash('Order berhasil diperbarui!', 'success')
        return redirect(url_for('orders.detail', id=id))
    
    shoe_types = ['Casual', 'Formal', 'Olahraga', 'Sneaker', 'Boot', 'Sepatu Kerja', 'Lainnya']
    status_options = [
        ('diterima', 'Diterima'),
        ('proses', 'Sedang Diproses'),
        ('selesai', 'Selesai'),
        ('diambil', 'Sudah Diambil')
    ]
    
    return render_template('orders/form_edit.html', 
                         order=order, 
                         services=services,
                         shoe_types=shoe_types,
                         status_options=status_options)

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Detail Order"""
    order = Order.query.get_or_404(id)
    return render_template('orders/detail.html', order=order)
