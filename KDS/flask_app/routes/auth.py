from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ayarlar import CREDENTIALS
from database.auth_dao import authenticate

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        kullanici = authenticate(username, password)

        if kullanici:
            # Login başarılı
            session['logged_in'] = True
            session['logged_in_user'] = kullanici.get('kullaniciAdSoyad', username)
            session['user_id'] = kullanici.get('kullaniciId')
            session['kimlik_id'] = kullanici.get('kimlikId')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('😕 Kullanıcı adı/TC veya şifre hatalı', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
