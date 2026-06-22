from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required
from app import db, login_manager
from models import Admin

bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman Login Admin"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi!', 'danger')
            return redirect(url_for('auth.login'))
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password) and admin.is_active:
            login_user(admin)
            session.permanent = True
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Username atau password salah!', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout Admin"""
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('auth.login'))
