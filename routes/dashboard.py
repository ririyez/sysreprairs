from flask import Blueprint, render_template
from flask_login import login_required
from app import db
from models import Order, Customer, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """Dashboard utama"""
    # Total Pesanan
    total_orders = Order.query.count()
    
    # Reparasi Aktif (status: diterima atau proses)
    active_repairs = Order.query.filter(Order.status.in_(['diterima', 'proses'])).count()
    
    # Pendapatan Bulan Ini
    today = datetime.utcnow()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_income = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai',
        Order.completed_date >= first_day_of_month
    ).scalar() or 0
    
    # Total Pelanggan
    total_customers = Customer.query.count()
    
    # Pendapatan harian (7 hari terakhir)
    daily_income = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        income = db.session.query(func.sum(Order.total_price)).filter(
            Order.status == 'selesai',
            Order.completed_date.between(start, end)
        ).scalar() or 0
        
        daily_income.append({
            'date': date.strftime('%d-%m'),
            'income': float(income)
        })
    
    # Status Order (untuk chart)
    status_counts = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    status_data = {
        'diterima': 0,
        'proses': 0,
        'selesai': 0,
        'diambil': 0
    }
    for status, count in status_counts:
        if status in status_data:
            status_data[status] = count
    
    # Order terbaru
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    stats = {
        'total_orders': total_orders,
        'active_repairs': active_repairs,
        'monthly_income': monthly_income,
        'total_customers': total_customers,
        'daily_income': daily_income,
        'status_data': status_data,
        'recent_orders': recent_orders
    }
    
    return render_template('dashboard/index.html', stats=stats)
