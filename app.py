from flask import Flask, render_template, request, redirect, url_for, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import io
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # load .env if exists

app = Flask(__name__)
# Use env var DATABASE_URL for production; fallback to sqlite file for local
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///shoetra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-this')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='kasir')  # owner or kasir

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    # flask-login interface
    def is_active(self): return True
    def get_id(self): return str(self.id)
    def is_authenticated(self): return True
    def is_anonymous(self): return False

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    tracking_token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_name = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    item_desc = db.Column(db.String(300))
    price = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    stage = db.Column(db.Integer, default=0)  # 0..7 for 8 stages
    paid = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()
    return render_template('index.html', orders=orders)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.check_password(request.form['password']):
            login_user(u)
            return redirect(url_for('index'))
        return render_template('login.html', error='Login gagal')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/order/new', methods=['GET','POST'])
@login_required
def new_order():
    if request.method == 'POST':
        invoice_no = f"ST{int(datetime.utcnow().timestamp())}"
        due = request.form.get('due_date')
        order = Order(
            invoice_no=invoice_no,
            customer_name=request.form['customer_name'],
            phone=request.form.get('phone'),
            item_desc=request.form.get('item_desc'),
            price=int(request.form.get('price') or 0),
            due_date=datetime.fromisoformat(due) if due else None
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_order.html')

@app.route('/order/<int:order_id>/update_stage', methods=['POST'])
@login_required
def update_stage(order_id):
    order = Order.query.get_or_404(order_id)
    step = int(request.form.get('step', order.stage))
    order.stage = step
    db.session.commit()
    return redirect(url_for('index'))

# public tracking by token
@app.route('/track/<token>')
def public_track(token):
    order = Order.query.filter_by(tracking_token=token).first_or_404()
    stages = [
        "Diterima", "Pre-wash", "Brush", "Deep clean", "Drying",
        "Quality check", "Packaging", "Siap diambil"
    ]
    return render_template('public_track.html', order=order, stages=stages)

# Export orders to Excel
@app.route('/export/orders.xlsx')
@login_required
def export_orders():
    orders = Order.query.all()
    rows = []
    for o in orders:
        rows.append({
            'invoice_no': o.invoice_no,
            'customer': o.customer_name,
            'phone': o.phone,
            'price': o.price,
            'stage': o.stage,
            'created_at': o.created_at,
            'due_date': o.due_date,
        })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine='openpyxl')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='orders.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    # For quick local dev: create DB tables if missing
    with app.app_context():
        db.create_all()
    app.run(debug=True)