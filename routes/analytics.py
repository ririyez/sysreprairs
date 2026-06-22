from flask import Blueprint, render_template
from flask_login import login_required
from app import db
from models import Order, Service
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
@login_required
def index():
    """Dashboard Analitik"""
    # Grafik Pendapatan (12 bulan terakhir)
    today = datetime.utcnow()
    revenue_data = []
    
    for i in range(11, -1, -1):
        date = today - timedelta(days=30*i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if date.month == 12:
            next_month = date.replace(year=date.year+1, month=1, day=1)
        else:
            next_month = date.replace(month=date.month+1, day=1)
        
        revenue = db.session.query(func.sum(Order.total_price)).filter(
            Order.status == 'selesai',
            Order.completed_date >= month_start,
            Order.completed_date < next_month
        ).scalar() or 0
        
        revenue_data.append({
            'month': date.strftime('%b'),
            'revenue': float(revenue)
        })
    
    # Status Order (pie chart)
    status_data = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    status_breakdown = {}
    status_labels = {
        'diterima': 'Diterima',
        'proses': 'Sedang Diproses',
        'selesai': 'Selesai',
        'diambil': 'Sudah Diambil'
    }
    
    for status, count in status_data:
        status_breakdown[status_labels.get(status, status)] = count
    
    # Layanan Terlaris
    service_data = db.session.query(
        Service.name,
        func.count(Order.id).label('count'),
        func.sum(Order.total_price).label('revenue')
    ).join(Order).group_by(Service.name).order_by(func.count(Order.id).desc()).limit(10).all()
    
    top_services = []
    for service_name, count, revenue in service_data:
        top_services.append({
            'name': service_name,
            'count': count,
            'revenue': float(revenue or 0)
        })
    
    # Statistik Umum
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai'
    ).scalar() or 0
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    stats = {
        'revenue_data': revenue_data,
        'status_breakdown': status_breakdown,
        'top_services': top_services,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value
    }
    
    return render_template('analytics/index.html', stats=stats)
