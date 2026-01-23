"""
Advanced Payroll Management System - Main Flask Application
Includes: Authentication, Dashboard, Attendance, Payroll Processing
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from models import Database, Employee, Attendance, Payroll, AdminLog, OTPVerification
from email_service import EmailService
from utils import PDFGenerator, ExcelHandler, BackupManager, get_current_month
from datetime import datetime, date
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Random secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PAYSLIP_FOLDER'] = 'payslips'
app.config['BACKUP_FOLDER'] = 'backups'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create required directories
for folder in ['uploads', 'payslips', 'backups', 'logs']:
    os.makedirs(folder, exist_ok=True)

# Initialize services
email_service = EmailService()
pdf_generator = PDFGenerator()

# ======================== HELPER FUNCTIONS ========================

def login_required(f):
    """Decorator to check if user is logged in"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'emp_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('employee_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action_type, description):
    """Log admin actions"""
    if 'emp_id' in session and session.get('role') == 'admin':
        admin_log = AdminLog()
        admin_log.log_action(
            session['emp_id'],
            action_type,
            description,
            request.remote_addr
        )

# ======================== AUTHENTICATION ROUTES ========================

@app.route('/')
def index():
    """Homepage - redirect based on login status"""
    if 'emp_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Employee registration with OTP verification"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        emp = Employee()
        if emp.get_by_email(email):
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        # Generate and send OTP
        otp_service = OTPVerification()
        otp = otp_service.generate_otp()
        
        if otp_service.save_otp(email, otp, 'registration'):
            if email_service.send_otp(email, otp, 'registration'):
                # Store registration data in session temporarily
                session['temp_registration'] = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'password': password
                }
                flash('OTP sent to your email! Please verify.', 'success')
                return redirect(url_for('verify_otp', purpose='registration'))
            else:
                flash('Failed to send OTP. Please check email configuration.', 'error')
        else:
            flash('Error generating OTP. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/verify-otp/<purpose>', methods=['GET', 'POST'])
def verify_otp(purpose):
    """OTP verification page"""
    if request.method == 'POST':
        otp = request.form['otp']
        
        if purpose == 'registration' and 'temp_registration' in session:
            reg_data = session['temp_registration']
            otp_service = OTPVerification()
            
            if otp_service.verify_otp(reg_data['email'], otp, 'registration'):
                # Create employee account
                emp = Employee()
                emp_id = emp.create({
                    'name': reg_data['name'],
                    'email': reg_data['email'],
                    'phone': reg_data['phone'],
                    'password': reg_data['password'],
                    'department': 'General',
                    'designation': 'Employee',
                    'joining_date': date.today(),
                    'base_salary': 30000.00,
                    'role': 'employee'
                })
                
                if emp_id:
                    # Send welcome email
                    email_service.send_registration_success(
                        reg_data['email'],
                        reg_data['name'],
                        emp_id
                    )
                    
                    # Clear temporary data
                    session.pop('temp_registration', None)
                    
                    flash(f'Registration successful! Your Employee ID: {emp_id}', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Registration failed. Please try again.', 'error')
            else:
                flash('Invalid or expired OTP!', 'error')
        
        elif purpose == 'login' and 'temp_login_email' in session:
            email = session['temp_login_email']
            otp_service = OTPVerification()
            
            if otp_service.verify_otp(email, otp, 'login'):
                emp = Employee()
                employee = emp.get_by_email(email)
                
                if employee:
                    # Update OTP verified status
                    emp.update_status(employee['emp_id'], 'Active')
                    
                    # Create session
                    session['emp_id'] = employee['emp_id']
                    session['name'] = employee['name']
                    session['email'] = employee['email']
                    session['role'] = employee['role']
                    
                    session.pop('temp_login_email', None)
                    
                    if employee['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    return redirect(url_for('employee_dashboard'))
            else:
                flash('Invalid or expired OTP!', 'error')
        
        elif purpose == 'password_reset' and 'temp_reset_email' in session:
            email = session['temp_reset_email']
            new_password = session.get('temp_new_password')
            
            otp_service = OTPVerification()
            if otp_service.verify_otp(email, otp, 'password_reset'):
                emp = Employee()
                employee = emp.get_by_email(email)
                
                if employee and new_password:
                    # Update password
                    connection = emp.db.get_connection()
                    if connection:
                        cursor = connection.cursor()
                        password_hash = emp.hash_password(new_password)
                        cursor.execute(
                            "UPDATE employees SET password_hash = %s WHERE email = %s",
                            (password_hash, email)
                        )
                        connection.commit()
                        cursor.close()
                        connection.close()
                        
                        # Send confirmation email
                        email_service.send_password_reset(email, employee['name'], new_password)
                        
                        session.pop('temp_reset_email', None)
                        session.pop('temp_new_password', None)
                        
                        flash('Password reset successful! Please login.', 'success')
                        return redirect(url_for('login'))
            else:
                flash('Invalid or expired OTP!', 'error')
    
    return render_template('verify_otp.html', purpose=purpose)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Employee login with OTP verification"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        emp = Employee()
        employee = emp.get_by_email(email)
        
        if employee:
            # Check if account is active
            if employee['status'] != 'Active':
                flash('Your account is inactive. Contact admin.', 'error')
                return render_template('login.html')
            
            # Verify password
            if emp.verify_password(password, employee['password_hash']):
                # For first-time login or security, send OTP
                if not employee['otp_verified']:
                    otp_service = OTPVerification()
                    otp = otp_service.generate_otp()
                    
                    if otp_service.save_otp(email, otp, 'login'):
                        if email_service.send_otp(email, otp, 'login'):
                            session['temp_login_email'] = email
                            flash('OTP sent to your email for verification!', 'success')
                            return redirect(url_for('verify_otp', purpose='login'))
                
                # Direct login if already verified
                session['emp_id'] = employee['emp_id']
                session['name'] = employee['name']
                session['email'] = employee['email']
                session['role'] = employee['role']
                
                flash(f"Welcome back, {employee['name']}!", 'success')
                
                if employee['role'] == 'admin':
                    log_admin_action('login', f"Admin {employee['name']} logged in")
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('employee_dashboard'))
            else:
                flash('Invalid password!', 'error')
        else:
            flash('Email not found!', 'error')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - Reset via OTP"""
    if request.method == 'POST':
        email = request.form['email']
        
        emp = Employee()
        employee = emp.get_by_email(email)
        
        if employee:
            # Generate temporary password
            import secrets
            new_password = secrets.token_urlsafe(12)
            
            # Generate OTP
            otp_service = OTPVerification()
            otp = otp_service.generate_otp()
            
            if otp_service.save_otp(email, otp, 'password_reset'):
                if email_service.send_otp(email, otp, 'password reset'):
                    session['temp_reset_email'] = email
                    session['temp_new_password'] = new_password
                    flash('OTP sent to your email!', 'success')
                    return redirect(url_for('verify_otp', purpose='password_reset'))
        else:
            flash('Email not found!', 'error')
    
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    name = session.get('name')
    session.clear()
    flash(f'Goodbye {name}! Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ======================== ADMIN ROUTES ========================

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    emp = Employee()
    payroll = Payroll()
    
    # Get statistics
    all_employees = emp.get_all(include_inactive=True)
    active_employees = [e for e in all_employees if e['status'] == 'Active']
    inactive_employees = [e for e in all_employees if e['status'] == 'Inactive']
    
    # Department-wise count
    departments = {}
    for e in active_employees:
        dept = e.get('department', 'General')
        departments[dept] = departments.get(dept, 0) + 1
    
    # Monthly payroll summary (last 6 months)
    connection = emp.db.get_connection()
    monthly_payroll = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT month, SUM(net_salary) as total_payout, COUNT(*) as emp_count
            FROM payroll
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly_payroll = cursor.fetchall()
        cursor.close()
        connection.close()
    
    # Recent admin logs
    admin_log = AdminLog()
    recent_logs = admin_log.get_logs(limit=10)
    
    stats = {
        'total_employees': len(all_employees),
        'active_employees': len(active_employees),
        'inactive_employees': len(inactive_employees),
        'departments': departments,
        'monthly_payroll': monthly_payroll
    }
    
    return render_template('admin_dashboard.html', stats=stats, logs=recent_logs)

@app.route('/admin/employees')
@login_required
@admin_required
def admin_employees():
    """View all employees"""
    emp = Employee()
    employees = emp.get_all(include_inactive=True)
    return render_template('admin_employees.html', employees=employees)

@app.route('/admin/add-employee', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_employee():
    """Add new employee (Admin)"""
    if request.method == 'POST':
        emp = Employee()
        
        # Generate temporary password
        temp_password = secrets.token_urlsafe(12)
        
        emp_id = emp.create({
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'department': request.form['department'],
            'designation': request.form['designation'],
            'joining_date': request.form['joining_date'],
            'base_salary': float(request.form['base_salary']),
            'password': temp_password,
            'role': request.form.get('role', 'employee')
        })
        
        if emp_id:
            # Send email with credentials
            email_service.send_registration_success(
                request.form['email'],
                request.form['name'],
                emp_id
            )
            
            log_admin_action('employee_added', f"Added employee {emp_id}")
            flash(f'Employee added successfully! ID: {emp_id}', 'success')
            return redirect(url_for('admin_employees'))
        else:
            flash('Failed to add employee!', 'error')
    
    return render_template('admin_add_employee.html')

@app.route('/admin/deactivate-employee/<emp_id>')
@login_required
@admin_required
def admin_deactivate_employee(emp_id):
    """Deactivate employee (Soft delete)"""
    emp = Employee()
    if emp.update_status(emp_id, 'Inactive'):
        log_admin_action('employee_deactivated', f"Deactivated employee {emp_id}")
        flash('Employee deactivated successfully!', 'success')
    else:
        flash('Failed to deactivate employee!', 'error')
    return redirect(url_for('admin_employees'))

@app.route('/admin/activate-employee/<emp_id>')
@login_required
@admin_required
def admin_activate_employee(emp_id):
    """Reactivate employee"""
    emp = Employee()
    if emp.update_status(emp_id, 'Active'):
        log_admin_action('employee_activated', f"Activated employee {emp_id}")
        flash('Employee activated successfully!', 'success')
    else:
        flash('Failed to activate employee!', 'error')
    return redirect(url_for('admin_employees'))

@app.route('/admin/bulk-upload', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_bulk_upload():
    """Bulk employee upload via Excel"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read Excel
            employees_data, error = ExcelHandler.read_employee_excel(filepath)
            
            if error:
                flash(f'Error reading Excel: {error}', 'error')
                return redirect(request.url)
            
            # Add employees
            emp = Employee()
            success_count = 0
            failed_count = 0
            
            for emp_data in employees_data:
                # Generate temp password
                emp_data['password'] = secrets.token_urlsafe(12)
                
                emp_id = emp.create(emp_data)
                if emp_id:
                    success_count += 1
                    # Send email
                    email_service.send_registration_success(
                        emp_data['email'],
                        emp_data['name'],
                        emp_id
                    )
                else:
                    failed_count += 1
            
            log_admin_action('bulk_upload', f"Uploaded {success_count} employees")
            flash(f'Success: {success_count}, Failed: {failed_count}', 'success')
            return redirect(url_for('admin_employees'))
        else:
            flash('Invalid file format! Use .xlsx or .xls', 'error')
    
    return render_template('admin_bulk_upload.html')

@app.route('/admin/attendance')
@login_required
@admin_required
def admin_attendance():
    """View all attendance records"""
    month = request.args.get('month', get_current_month())
    
    emp = Employee()
    employees = emp.get_all()
    
    attendance_data = []
    att = Attendance()
    
    for employee in employees:
        records = att.get_monthly(employee['emp_id'], month)
        days_present = att.get_days_present(employee['emp_id'], month)
        
        attendance_data.append({
            'employee': employee,
            'days_present': days_present,
            'records': records
        })
    
    return render_template('admin_attendance.html', 
                         attendance_data=attendance_data, 
                         month=month)

@app.route('/admin/process-payroll', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_process_payroll():
    """Process monthly payroll for all employees"""
    if request.method == 'POST':
        month = request.form['month']
        
        emp = Employee()
        employees = emp.get_all()
        
        payroll = Payroll()
        pdf_gen = PDFGenerator()
        
        success_count = 0
        failed_count = 0
        
        for employee in employees:
            # Calculate salary
            salary_data = payroll.calculate_salary(employee['emp_id'], month)
            
            if salary_data:
                # Generate PDF
                pdf_filename = f"{employee['emp_id']}_{month}.pdf"
                pdf_path = os.path.join(app.config['PAYSLIP_FOLDER'], pdf_filename)
                
                if pdf_gen.generate_payslip(employee, salary_data, pdf_path):
                    # Save to database
                    trans_id = payroll.save_payroll(salary_data, pdf_path)
                    
                    if trans_id:
                        # Send email with payslip
                        email_service.send_payslip(
                            employee['email'],
                            employee['name'],
                            month,
                            salary_data['net_salary'],
                            pdf_path
                        )
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        
        log_admin_action('payroll_processed', f"Processed payroll for {month}")
        flash(f'Payroll processed! Success: {success_count}, Failed: {failed_count}', 'success')
        return redirect(url_for('admin_payroll'))
    
    return render_template('admin_process_payroll.html', current_month=get_current_month())

@app.route('/admin/payroll')
@login_required
@admin_required
def admin_payroll():
    """View payroll history"""
    month = request.args.get('month', get_current_month())
    
    emp = Employee()
    connection = emp.db.get_connection()
    
    payroll_records = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, e.name, e.department
            FROM payroll p
            JOIN employees e ON p.emp_id = e.emp_id
            WHERE p.month = %s
            ORDER BY p.trans_id DESC
        """, (month,))
        payroll_records = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('admin_payroll.html', records=payroll_records, month=month)

@app.route('/admin/backup')
@login_required
@admin_required
def admin_backup():
    """Create system backup"""
    if BackupManager.full_backup():
        log_admin_action('system_backup', 'Created full system backup')
        flash('System backup completed successfully!', 'success')
    else:
        flash('Backup failed!', 'error')
    return redirect(url_for('admin_dashboard'))

# ======================== EMPLOYEE ROUTES ========================

@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    """Employee dashboard"""
    emp = Employee()
    employee = emp.get_by_id(session['emp_id'])
    
    # Get recent attendance
    att = Attendance()
    current_month = get_current_month()
    attendance_records = att.get_monthly(session['emp_id'], current_month)
    days_present = att.get_days_present(session['emp_id'], current_month)
    
    # Get recent payslips
    payroll = Payroll()
    payslips = payroll.get_employee_payslips(session['emp_id'])
    
    return render_template('employee_dashboard.html',
                         employee=employee,
                         attendance_records=attendance_records,
                         days_present=days_present,
                         payslips=payslips[:3])

@app.route('/employee/mark-attendance', methods=['POST'])
@login_required
def employee_mark_attendance():
    """Mark daily attendance"""
    att = Attendance()
    today = date.today()
    
    # Check if already marked
    existing = att.get_monthly(session['emp_id'], today.strftime('%Y-%m'))
    today_record = [r for r in existing if r['date'] == today]
    
    if today_record:
        flash('Attendance already marked for today!', 'warning')
    else:
        check_in_time = datetime.now().strftime('%H:%M:%S')
        
        if att.mark(session['emp_id'], today, 'Present', check_in_time):
            flash('Attendance marked successfully!', 'success')
        else:
            flash('Failed to mark attendance!', 'error')
    
    return redirect(url_for('employee_dashboard'))

@app.route('/employee/attendance')
@login_required
def employee_attendance():
    """View attendance history"""
    month = request.args.get('month', get_current_month())
    
    att = Attendance()
    attendance_records = att.get_monthly(session['emp_id'], month)
    days_present = att.get_days_present(session['emp_id'], month)
    
    return render_template('employee_attendance.html',
                         attendance_records=attendance_records,
                         days_present=days_present,
                         month=month)

@app.route('/employee/payslips')
@login_required
def employee_payslips():
    """View all payslips"""
    payroll = Payroll()
    payslips = payroll.get_employee_payslips(session['emp_id'])
    
    return render_template('employee_payslips.html', payslips=payslips)

@app.route('/download-payslip/<int:trans_id>')
@login_required
def download_payslip(trans_id):
    """Download payslip PDF"""
    payroll = Payroll()
    connection = payroll.db.get_connection()
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payroll WHERE trans_id = %s", (trans_id,))
        record = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if record and record['pdf_path']:
            # Check if employee owns this payslip or is admin
            if record['emp_id'] == session['emp_id'] or session.get('role') == 'admin':
                if os.path.exists(record['pdf_path']):
                    return send_file(record['pdf_path'], as_attachment=True)
                else:
                    flash('Payslip file not found!', 'error')
            else:
                flash('Unauthorized access!', 'error')
        else:
            flash('Payslip not found!', 'error')
    
    return redirect(url_for('employee_payslips'))

# ======================== RUN APPLICATION ========================

if __name__ == '__main__':
    # Initialize database
    print("\n🔧 Initializing database...")
    db = Database()
    db.create_database_and_tables()
    
    print("\n🚀 Starting Flask application...")
    print("📍 Access at: http://localhost:5000")
    print("\n" + "="*50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)