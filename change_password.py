# change_password.py
from app import app, db, User

with app.app_context():
    username = 'owner'   # ganti jika username berbeda
    new_pw = 'password_baru_Anda'  # ganti jadi password yang Anda mau
    u = User.query.filter_by(username=username).first()
    if not u:
        print(f"User {username} tidak ditemukan")
    else:
        u.set_password(new_pw)
        db.session.commit()
        print(f"Password user {username} berhasil diubah")