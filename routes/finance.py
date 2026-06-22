from flask import Blueprint, render_template, request
from flask_login import login_required
from app import db
from models import Order, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func, extract

bp = Blueprint('finance', __name__, url_prefix='/finance')

@bp.route('/')
@login_required
def index():
    """Dashboard Keuangan"""
    today = datetime.utcnow()
    
    # Pendapatan Hari Ini
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    today_income = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai',
        Order.completed_date.between(today_start, today_end)
    ).scalar() or 0
    
    # Pendapatan Bulan Ini
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_income = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai',
        Order.completed_date >= first_day_of_month
    ).scalar() or 0
    
    # Pendapatan Tahun Ini
    first_day_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    yearly_income = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai',
        Order.completed_date >= first_day_of_year
    ).scalar() or 0
    
    # Pendapatan Harian (30 hari terakhir)
    daily_income = []
    for i in range(29, -1, -1):
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
    
    # Pendapatan Bulanan (12 bulan terakhir)
    monthly_income_data = []
    for i in range(11, -1, -1):
        date = today - timedelta(days=30*i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Hitung hari pertama bulan berikutnya
        if date.month == 12:
            next_month = date.replace(year=date.year+1, month=1, day=1)
        else:
            next_month = date.replace(month=date.month+1, day=1)
        
        income = db.session.query(func.sum(Order.total_price)).filter(
            Order.status == 'selesai',
            Order.completed_date >= month_start,
            Order.completed_date < next_month
        ).scalar() or 0
        
        monthly_income_data.append({
            'month': date.strftime('%b %Y'),
            'income': float(income)
        })
    
    stats = {
        'today_income': today_income,
        'monthly_income': monthly_income,
        'yearly_income': yearly_income,
        'daily_income': daily_income,
        'monthly_income_data': monthly_income_data
    }
    
    return render_template('finance/index.html', stats=stats)

@bp.route('/laporan')
@login_required
def laporan():
    """Laporan Transaksi"""
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Order.query.filter_by(status='selesai')
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.completed_date >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.completed_date <= end)
        except:
            pass
    
    total_revenue = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'selesai'
    ).scalar() or 0
    
    if start_date or end_date:
        total_revenue = db.session.query(func.sum(Order.total_price)).filter(
            Order.status == 'selesai',
            query.whereclause
        ).scalar() or 0
    
    orders = query.order_by(Order.completed_date.desc()).paginate(page=page, per_page=20)
    
    return render_template('finance/laporan.html', 
                         orders=orders,
                         start_date=start_date,
                         end_date=end_date,
                         total_revenue=total_revenue)
