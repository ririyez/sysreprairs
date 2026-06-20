# Helper quick script to create DB and default user
from app import db, User
from app import app

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='owner').first():
        u = User(username='owner', role='owner')
        u.set_password('owner123')  # ganti nanti
        db.session.add(u)
        db.session.commit()
        print("Created user 'owner' with password 'owner123' (please change!)")
    else:
        print("User 'owner' already exists")