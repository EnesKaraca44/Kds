from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CREDENTIALS

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username in CREDENTIALS and str(CREDENTIALS[username]) == password:
            session['logged_in'] = True
            session['logged_in_user'] = username
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('😕 Kullanıcı adı veya şifre hatalı', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
