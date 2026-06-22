from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

class Admin(UserMixin, db.Model):
    """Model Admin"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash dan set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifikasi password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Customer(db.Model):
    """Model Pelanggan"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    province = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Service(db.Model):
    """Model Jenis Layanan"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    base_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name}>'

class Order(db.Model):
    """Model Order Reparasi"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    
    # Detail Sepatu
    shoe_type = db.Column(db.String(100), nullable=False)  # Casual, Formal, Olahraga, dll
    shoe_brand = db.Column(db.String(100), nullable=False)
    shoe_color = db.Column(db.String(50), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    
    # Harga
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='diterima')  # diterima, proses, selesai, diambil
    progress_percentage = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    
    # Foto
    before_photo = db.Column(db.String(255), nullable=True)
    after_photo = db.Column(db.String(255), nullable=True)
    
    # Waktu
    received_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.invoice_number}>'
    
    def get_status_display(self):
        """Tampilkan status dalam Bahasa Indonesia"""
        status_map = {
            'diterima': 'Diterima',
            'proses': 'Sedang Diproses',
            'selesai': 'Selesai',
            'diambil': 'Sudah Diambil'
        }
        return status_map.get(self.status, self.status)

class Transaction(db.Model):
    """Model Transaksi Keuangan"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    transaction_type = db.Column(db.String(50), nullable=False)  # income, expense
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, transfer, card
    reference_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type}>'
