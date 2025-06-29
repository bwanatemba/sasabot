from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import Admin, Vendor
from services.auth.auth_manager import get_user_role
from services.auth.decorators import admin_required, vendor_required
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_phone = request.form.get('email_or_phone')
        password = request.form.get('password')
        
        if not email_or_phone or not password:
            flash('Email/Phone and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Try to find admin first
        user = Admin.objects(email=email_or_phone).first() or Admin.objects(phone_number=email_or_phone).first()
        
        # If not admin, try vendor
        if not user:
            user = Vendor.objects(email=email_or_phone).first() or Vendor.objects(phone_number=email_or_phone).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            
            # Redirect based on user role
            role = get_user_role(user)
            if role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            elif role == 'vendor':
                return redirect(next_page) if next_page else redirect(url_for('vendor.dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.password = generate_password_hash(new_password)
        current_user.save()
        
        flash('Password changed successfully.', 'success')
        
        # Redirect based on user role
        role = get_user_role(current_user)
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('vendor.dashboard'))
    
    return render_template('auth/change_password.html')
