from flask import Blueprint, render_template, request, jsonify
from models import Order, Customer

bp = Blueprint('tracking', __name__, url_prefix='/tracking')

@bp.route('/')
def index():
    """Halaman Tracking Publik"""
    return render_template('tracking/index.html')

@bp.route('/cek', methods=['POST'])
def cek():
    """Cek status order berdasarkan nomor invoice"""
    invoice_number = request.form.get('invoice_number', '').strip().upper()
    
    if not invoice_number:
        return jsonify({'error': 'Nomor invoice harus diisi'}), 400
    
    order = Order.query.filter_by(invoice_number=invoice_number).first()
    
    if not order:
        return jsonify({'error': 'Nomor invoice tidak ditemukan'}), 404
    
    # Status mapping
    status_colors = {
        'diterima': 'primary',
        'proses': 'warning',
        'selesai': 'success',
        'diambil': 'info'
    }
    
    status_messages = {
        'diterima': 'Pesanan Diterima',
        'proses': 'Sedang Diproses',
        'selesai': 'Selesai Dikerjakan',
        'diambil': 'Sudah Diambil'
    }
    
    data = {
        'invoice_number': order.invoice_number,
        'customer_name': order.customer.name,
        'status': order.status,
        'status_display': status_messages.get(order.status, order.status),
        'status_color': status_colors.get(order.status, 'secondary'),
        'progress': order.progress_percentage,
        'shoe_type': order.shoe_type,
        'shoe_brand': order.shoe_brand,
        'shoe_color': order.shoe_color,
        'complaint': order.complaint,
        'received_date': order.received_date.strftime('%d-%m-%Y %H:%M'),
        'before_photo': f'/uploads/{order.before_photo}' if order.before_photo else None,
        'after_photo': f'/uploads/{order.after_photo}' if order.after_photo else None,
        'total_price': f'Rp {order.total_price:,.0f}',
    }
    
    if order.completed_date:
        data['completed_date'] = order.completed_date.strftime('%d-%m-%Y %H:%M')
    
    return jsonify(data)
