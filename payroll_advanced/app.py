""" Advanced Payroll Management System """

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from models import Database, Employee, Attendance, Payroll, AdminLog, OTPVerification
from email_service import EmailService
from utils import PDFGenerator, ExcelHandler, BackupManager, get_current_month
from datetime import datetime, date
import os
import secrets
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PAYSLIP_FOLDER'] = 'payslips'
app.config['BACKUP_FOLDER'] = 'backups'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create directories
for folder in ['uploads', 'payslips', 'backups', 'logs']:
    os.makedirs(folder, exist_ok=True)

# Initialize services
email_service = EmailService()
pdf_generator = PDFGenerator()

# ======================== FIX 1: DISABLE CACHE ========================
@app.after_request
def add_header(response):
    """Prevent browser caching - ensures fresh data"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ======================== DECORATORS ========================

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'emp_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('employee_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action_type, description):
    if 'emp_id' in session and session.get('role') == 'admin':
        admin_log = AdminLog()
        admin_log.log_action(session['emp_id'], action_type, description, request.remote_addr)

# ======================== AUTHENTICATION ========================

@app.route('/')
def index():
    if 'emp_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - Step 1: Collect details and send OTP"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form.get('phone', '')
        
        # Validate passwords match
        if password != confirm_password:
            flash('❌ Passwords do not match!', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        emp = Employee()
        if emp.get_by_email(email):
            flash('❌ Email already registered!', 'error')
            return render_template('register.html')
        
        # Generate OTP
        import random
        otp_code = str(random.randint(100000, 999999))
        
        print(f"\n📧 REGISTRATION OTP:")
        print(f"   Email: {email}")
        print(f"   OTP: {otp_code}")
        
        # Save OTP to database - FIXED METHOD NAME
        otp = OTPVerification()
        if otp.save_otp(email, otp_code, purpose='registration'):  # ← FIXED HERE
            # Try to send email
            email_sent = email_service.send_otp(email, otp_code, purpose='registration')
            
            # Store registration data in session
            session['registration_data'] = {
                'name': name,
                'email': email,
                'password': password,
                'phone': phone
            }
            
            if email_sent:
                flash(f'✅ OTP sent to {email}! Check your inbox.', 'success')
            else:
                # If email fails, show OTP in flash (for testing)
                flash(f'⚠️ Email service unavailable. Your OTP is: {otp_code}', 'warning')
            
            return redirect(url_for('verify_registration_otp'))
        else:
            flash('❌ System error. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/verify-registration-otp', methods=['GET', 'POST'])
def verify_registration_otp():
    """Step 2: Verify OTP and complete registration"""
    
    # Check if registration data exists in session
    if 'registration_data' not in session:
        flash('❌ Invalid session. Please register again.', 'error')
        return redirect(url_for('register'))
    
    registration_data = session['registration_data']
    email = registration_data['email']
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '')
        
        print(f"\n🔍 VERIFYING REGISTRATION OTP:")
        print(f"   Email: {email}")
        print(f"   OTP entered: {otp_code}")
        
        # Verify OTP
        otp = OTPVerification()
        if otp.verify_otp(email, otp_code, purpose='registration'):
            print(f"✅ OTP VERIFIED!")
            
            # Create employee account
            emp = Employee()
            emp_id = emp.create({
                'name': registration_data['name'],
                'email': registration_data['email'],
                'password': registration_data['password'],
                'phone': registration_data.get('phone'),
                'department': 'General',
                'designation': 'Employee',
                'joining_date': date.today(),
                'base_salary': 30000.00,
                'role': 'employee'
            })
            
            if emp_id:
                # Mark OTP as verified
                emp.mark_otp_verified(email)
                
                # Send welcome email
                try:
                    email_service.send_welcome_email(email, registration_data['name'], emp_id)
                except:
                    pass
                
                # Clear session
                session.pop('registration_data', None)
                
                print(f"✅ REGISTRATION COMPLETE: {emp_id}")
                flash(f'✅ Registration successful! Your Employee ID: {emp_id}', 'success')
                return redirect(url_for('login'))
            else:
                flash('❌ Failed to create account. Please try again.', 'error')
        else:
            print(f"❌ INVALID OTP!")
            flash('❌ Invalid or expired OTP. Please try again.', 'error')
    
    return render_template('verify_otp.html', email=email, purpose='registration')


@app.route('/resend-registration-otp', methods=['POST'])
def resend_registration_otp():
    """Resend OTP for registration"""
    
    if 'registration_data' not in session:
        flash('❌ Invalid session. Please register again.', 'error')
        return redirect(url_for('register'))
    
    email = session['registration_data']['email']
    
    # Generate new OTP
    import random
    otp_code = str(random.randint(100000, 999999))
    
    print(f"\n🔄 RESENDING REGISTRATION OTP:")
    print(f"   Email: {email}")
    print(f"   New OTP: {otp_code}")
    
    # Save OTP
    otp = OTPVerification()
    if otp.create_otp(email, otp_code, purpose='registration'):
        # Send email
        email_sent = email_service.send_otp(email, otp_code, purpose='registration')
        
        if email_sent:
            flash(f'✅ New OTP sent to {email}!', 'success')
        else:
            flash(f'⚠️ Email unavailable. Your new OTP is: {otp_code}', 'warning')
    else:
        flash('❌ Failed to generate OTP. Please try again.', 'error')
    
    return redirect(url_for('verify_registration_otp'))


# ============================================================================
# ADD THIS HELPER METHOD TO Employee CLASS IN models.py
# ============================================================================

def mark_otp_verified(self, email):
    """Mark employee's OTP as verified"""
    connection = self.db.get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE employees SET otp_verified = TRUE WHERE email = %s",
                (email,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"❌ Error marking OTP verified: {e}")
            return False
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        print(f"\n🔍 Login attempt: {email}")
        
        emp = Employee()
        employee = emp.get_by_email(email)
        
        if not employee:
            flash('Email not found!', 'error')
            return render_template('login.html')
        
        if employee['status'] != 'Active':
            flash('Your account is inactive. Contact admin.', 'error')
            return render_template('login.html')
        
        # Verify password
        password_valid = False
        try:
            if emp.verify_password(password, employee['password_hash']):
                password_valid = True
        except:
            sha_hash = hashlib.sha256(password.encode()).hexdigest()
            if sha_hash == employee['password_hash']:
                password_valid = True
        
        if password_valid:
            session['emp_id'] = employee['emp_id']
            session['name'] = employee['name']
            session['email'] = employee['email']
            session['role'] = employee['role']
            
            flash(f"Welcome back, {employee['name']}!", 'success')
            
            if employee['role'] == 'admin':
                log_admin_action('login', f"Admin logged in")
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    name = session.get('name')
    session.clear()
    flash(f'Goodbye {name}!', 'success')
    return redirect(url_for('login'))

# ======================== FORGOT PASSWORD ROUTES ========================

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - Send OTP"""
    if request.method == 'POST':
        email = request.form.get('email', '')
        
        print(f"\n📧 Password reset request for: {email}")
        
        emp = Employee()
        employee = emp.get_by_email(email)
        
        if not employee:
            flash('Email not found!', 'error')
            return render_template('forgot_password.html')
        
        # Generate OTP
        import random
        otp_code = str(random.randint(100000, 999999))
        
        # Save OTP
        otp = OTPVerification()
        if otp.create_otp(email, otp_code, purpose='forgot_password'):
            # Send email
            if email_service.send_otp(email, otp_code, purpose='forgot_password'):
                session['reset_email'] = email
                flash(f'✅ Verification code sent to {email}!', 'success')
                return redirect(url_for('verify_reset_otp'))
            else:
                flash('❌ Failed to send email. Contact administrator.', 'error')
        else:
            flash('❌ System error. Please try again.', 'error')
    
    return render_template('forgot_password.html')


@app.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    """Verify OTP"""
    if 'reset_email' not in session:
        flash('Invalid session. Please start again.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '')
        email = session['reset_email']
        
        otp = OTPVerification()
        if otp.verify_otp(email, otp_code, purpose='forgot_password'):
            session['otp_verified'] = True
            flash('✅ OTP verified! Set your new password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('❌ Invalid or expired OTP.', 'error')
    
    return render_template('verify_reset_otp.html', email=session['reset_email'])


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password"""
    if 'reset_email' not in session or not session.get('otp_verified'):
        flash('Unauthorized access!', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('reset_password.html')
        
        email = session['reset_email']
        
        emp = Employee()
        employee = emp.get_by_email(email)
        
        if employee:
            # Hash password
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Update
            connection = emp.db.get_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE employees SET password_hash = %s WHERE email = %s",
                    (password_hash, email)
                )
                connection.commit()
                cursor.close()
                connection.close()
                
                # Send confirmation email
                email_service.send_password_reset_success(email, employee['name'])
                
                # Clear session
                session.pop('reset_email', None)
                session.pop('otp_verified', None)
                
                flash('✅ Password reset successfully! You can now login.', 'success')
                return redirect(url_for('login'))
        
        flash('❌ Failed to reset password.', 'error')
    
    return render_template('reset_password.html')

# ======================== ADMIN DASHBOARD ========================

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    emp = Employee()
    all_employees = emp.get_all(include_inactive=True)
    active_employees = [e for e in all_employees if e['status'] == 'Active']
    
    departments = {}
    for e in active_employees:
        dept = e.get('department', 'General')
        departments[dept] = departments.get(dept, 0) + 1
    
    connection = emp.db.get_connection()
    monthly_payroll = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT month, SUM(net_salary) as total_payout, COUNT(*) as emp_count
            FROM payroll GROUP BY month ORDER BY month DESC LIMIT 6
        """)
        monthly_payroll = cursor.fetchall()
        cursor.close()
        connection.close()
    
    admin_log = AdminLog()
    recent_logs = admin_log.get_logs(limit=10)
    
    stats = {
        'total_employees': len(all_employees),
        'active_employees': len(active_employees),
        'inactive_employees': len([e for e in all_employees if e['status'] == 'Inactive']),
        'departments': departments,
        'monthly_payroll': monthly_payroll
    }
    
    return render_template('admin_dashboard.html', stats=stats, logs=recent_logs)

# ======================== EMPLOYEE MANAGEMENT ========================

@app.route('/admin/employees')
@login_required
@admin_required
def admin_employees():
    emp = Employee()
    employees = emp.get_all(include_inactive=True)
    return render_template('admin_employees.html', employees=employees)

@app.route('/admin/add-employee', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_employee():
    if request.method == 'POST':
        emp = Employee()
        temp_password = secrets.token_urlsafe(12)
        
        emp_id = emp.create({
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form.get('phone'),
            'department': request.form['department'],
            'designation': request.form['designation'],
            'joining_date': request.form['joining_date'],
            'base_salary': float(request.form['base_salary']),
            'password': temp_password,
            'role': request.form.get('role', 'employee')
        })
        
        if emp_id:
            log_admin_action('employee_added', f"Added {emp_id}")
            flash(f'Employee added! ID: {emp_id}, Password: {temp_password}', 'success')
            return redirect(url_for('admin_employees'))
        flash('Failed!', 'error')
    
    return render_template('admin_add_employee.html')

@app.route('/admin/deactivate-employee/<emp_id>')
@login_required
@admin_required
def admin_deactivate_employee(emp_id):
    emp = Employee()
    if emp.update_status(emp_id, 'Inactive'):
        log_admin_action('employee_deactivated', f"Deactivated {emp_id}")
        flash('Employee deactivated!', 'success')
    else:
        flash('Failed!', 'error')
    return redirect(url_for('admin_employees'))

@app.route('/admin/activate-employee/<emp_id>')
@login_required
@admin_required
def admin_activate_employee(emp_id):
    emp = Employee()
    if emp.update_status(emp_id, 'Active'):
        log_admin_action('employee_activated', f"Activated {emp_id}")
        flash('Employee activated!', 'success')
    else:
        flash('Failed!', 'error')
    return redirect(url_for('admin_employees'))

# ======================== FIX 2: ATTENDANCE WITH DEBUG ========================

@app.route('/admin/attendance')
@login_required
@admin_required
def admin_attendance():
    month = request.args.get('month', get_current_month())
    
    # ADD THIS DEBUG
    print(f"\n" + "="*50)
    print(f"ADMIN ATTENDANCE PAGE")
    print(f"Month requested: {month}")
    
    emp = Employee()
    employees = emp.get_all()
    
    print(f"Total employees: {len(employees)}")
    
    attendance_data = []
    att = Attendance()
    
    for employee in employees:
        emp_id = employee['emp_id']
        records = att.get_monthly(emp_id, month)
        days_present = att.get_days_present(emp_id, month)
        
        # ADD THIS DEBUG
        print(f"{emp_id}: {len(records)} records, {days_present} days")
        
        attendance_data.append({
            'employee': employee,
            'days_present': days_present,
            'records': records
        })
    
    print(f"Total data: {len(attendance_data)}")
    print("="*50 + "\n")
    
    return render_template('admin_attendance.html', 
                         attendance_data=attendance_data,
                         month=month,
                         department='')

@app.route('/admin/mark-attendance', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_mark_attendance():
    """Mark attendance - WITH DEBUG LOGGING"""
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        date_str = request.form['date']
        status = request.form['status']
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        remarks = request.form.get('remarks')
        
        # DEBUG: Print what we're marking
        print(f"\n📝 MARKING ATTENDANCE:")
        print(f"   Employee: {emp_id}")
        print(f"   Date: {date_str}")
        print(f"   Status: {status}")
        print(f"   Check In: {check_in}")
        print(f"   Check Out: {check_out}")
        print(f"   Remarks: {remarks}")
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        month_str = attendance_date.strftime('%Y-%m')
        
        print(f"   Month extracted: {month_str}")
        
        # Check duplicate
        att = Attendance()
        existing = att.get_monthly(emp_id, month_str)
        duplicate = [r for r in existing if r['date'] == attendance_date]
        
        if duplicate:
            print(f"⚠️  DUPLICATE FOUND!")
            flash(f'⚠️ Attendance already marked for {emp_id} on {date_str}!', 'warning')
            return redirect(url_for('admin_mark_attendance'))
        
        # Mark attendance
        result = att.mark(emp_id, attendance_date, status, check_in, check_out, remarks)
        
        if result:
            print(f"✅ ATTENDANCE MARKED SUCCESSFULLY!")
            log_admin_action('attendance_marked', f"{status} for {emp_id}")
            flash('✅ Attendance marked successfully!', 'success')
            
            # CRITICAL FIX: Redirect with month parameter
            print(f"   Redirecting to: /admin/attendance?month={month_str}\n")
            return redirect(url_for('admin_attendance', month=month_str))
        else:
            print(f"❌ FAILED TO MARK ATTENDANCE!\n")
            flash('❌ Failed to mark attendance!', 'error')
    
    emp = Employee()
    employees = emp.get_all()
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('admin_mark_attendance.html', employees=employees, today=today)

@app.route('/admin/view-employee-attendance/<emp_id>')
@login_required
@admin_required
def admin_view_employee_attendance(emp_id):
    month = request.args.get('month', get_current_month())
    
    emp = Employee()
    employee = emp.get_by_id(emp_id)
    
    if not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('admin_attendance'))
    
    att = Attendance()
    records = att.get_monthly(emp_id, month)
    days_present = att.get_days_present(emp_id, month)
    
    print(f"\n📊 VIEW EMPLOYEE ATTENDANCE:")
    print(f"   Employee: {emp_id}")
    print(f"   Month: {month}")
    print(f"   Records: {len(records)}")
    print(f"   Days: {days_present}\n")
    
    return render_template('admin_view_employee_attendance.html',
                         employee=employee, records=records,
                         days_present=days_present, month=month)

# ======================== EMPLOYEE DASHBOARD ========================

@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    """Employee dashboard - WITH DEBUG LOGGING"""
    emp = Employee()
    employee = emp.get_by_id(session['emp_id'])
    
    att = Attendance()
    current_month = get_current_month()
    
    # DEBUG: Print what we're loading
    print(f"\n📊 EMPLOYEE DASHBOARD:")
    print(f"   Employee: {session['emp_id']}")
    print(f"   Month: {current_month}")
    
    attendance_records = att.get_monthly(session['emp_id'], current_month)
    days_present = att.get_days_present(session['emp_id'], current_month)
    
    # DEBUG: Print results
    print(f"   Records found: {len(attendance_records)}")
    print(f"   Days present: {days_present}\n")
    
    payroll = Payroll()
    payslips = payroll.get_employee_payslips(session['emp_id'])
    
    return render_template('employee_dashboard.html',
                         employee=employee,
                         attendance_records=attendance_records,
                         days_present=days_present,
                         payslips=payslips[:3])

@app.route('/employee/attendance')
@login_required
def employee_attendance():
    """Employee Attendance View - FIXED VERSION"""
    month = request.args.get('month', get_current_month())
    emp_id = session['emp_id']
    
    # Get attendance records
    att = Attendance()
    records = att.get_monthly(emp_id, month)
    
    # Calculate summary statistics
    total_days = len(records)
    present = sum(1 for r in records if r['status'] == 'Present')
    absent = sum(1 for r in records if r['status'] == 'Absent')
    leaves = sum(1 for r in records if r['status'] == 'Leave')
    half_days = sum(1 for r in records if r['status'] == 'Half-Day')
    
    # Create summary dictionary
    summary = {
        'total_days': total_days,
        'present': present,
        'absent': absent,
        'leaves': leaves,
        'half_days': half_days
    }
    
    return render_template('employee_attendance.html',
                         records=records,
                         summary=summary,
                         month=month)
@app.route('/employee/payslips')
@login_required
def employee_payslips():
    payroll = Payroll()
    payslips = payroll.get_employee_payslips(session['emp_id'])
    return render_template('employee_payslips.html', payslips=payslips)

# ======================== PAYROLL ========================

@app.route('/admin/process-payroll', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_process_payroll():
    """
    Improved payroll processing with comprehensive debugging and error handling
    """
    if request.method == 'POST':
        month = request.form['month']
        
        print(f"\n{'='*60}")
        print(f"PROCESSING PAYROLL FOR: {month}")
        print(f"{'='*60}")
        
        emp = Employee()
        employees = emp.get_all()
        
        print(f"📊 Found {len(employees)} total employees")
        
        # Filter only active employees
        active_employees = [e for e in employees if e.get('status') == 'Active']
        print(f"✅ {len(active_employees)} active employees")
        
        if not active_employees:
            flash('❌ No active employees found to process payroll!', 'error')
            return redirect(url_for('admin_process_payroll'))
        
        payroll = Payroll()
        success_count = 0
        failed_count = 0
        no_attendance_count = 0
        
        for employee in active_employees:
            emp_id = employee['emp_id']
            print(f"\n📋 Processing: {emp_id} - {employee['name']}")
            
            # Check if already processed
            connection = payroll.db.get_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM payroll WHERE emp_id = %s AND month = %s", (emp_id, month))
                existing = cursor.fetchone()[0]
                cursor.close()
                connection.close()
                
                if existing > 0:
                    print(f"   ⏭️  Already processed - skipping")
                    continue
            
            # Calculate salary
            salary_data = payroll.calculate_salary(emp_id, month)
            
            if not salary_data:
                print(f"   ❌ Failed to calculate salary")
                failed_count += 1
                continue
            
            # Check if employee has attendance
            if salary_data['days_present'] == 0:
                print(f"   ⚠️  No attendance records found")
                no_attendance_count += 1
                # Still process but with 0 days
            
            print(f"   Days: {salary_data['days_present']}/{salary_data['total_days']}")
            print(f"   Net Salary: ₹{salary_data['net_salary']:,.2f}")
            
            # Generate PDF
            pdf_filename = f"{emp_id}_{month}.pdf"
            pdf_path = os.path.join(app.config['PAYSLIP_FOLDER'], pdf_filename)
            
            try:
                if pdf_generator.generate_payslip(employee, salary_data, pdf_path):
                    print(f"   ✅ PDF generated")
                else:
                    print(f"   ⚠️  PDF generation failed, saving without PDF")
                    pdf_path = None
            except Exception as e:
                print(f"   ⚠️  PDF error: {e}, saving without PDF")
                pdf_path = None
            
            # Save payroll record
            try:
                if payroll.save_payroll(salary_data, pdf_path):
                    print(f"   ✅ Payroll record saved")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to save payroll record")
                    failed_count += 1
            except Exception as e:
                print(f"   ❌ Error saving: {e}")
                import traceback
                traceback.print_exc()
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"PAYROLL PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successfully processed: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⚠️  No attendance: {no_attendance_count}")
        print(f"{'='*60}\n")
        
        log_admin_action('payroll_processed', f"Processed {month}: {success_count} success, {failed_count} failed")
        
        if success_count > 0:
            flash(f'✅ Payroll processed! Success: {success_count} | Failed: {failed_count} | No Attendance: {no_attendance_count}', 'success')
        else:
            flash(f'⚠️ Payroll processing completed with issues. Success: {success_count} | Failed: {failed_count} | No Attendance: {no_attendance_count}', 'warning')
        
        return redirect(url_for('admin_payroll', month=month))
    
    return render_template('admin_process_payroll.html', current_month=get_current_month())

@app.route('/admin/check-salary/<emp_id>')
@login_required
@admin_required
def admin_check_salary(emp_id):
    """Check individual employee salary calculation before processing"""
    month = request.args.get('month', get_current_month())
    
    emp = Employee()
    employee = emp.get_by_id(emp_id)
    
    if not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('admin_employees'))
    
    # Get attendance
    att = Attendance()
    attendance_records = att.get_monthly(emp_id, month)
    days_present = att.get_days_present(emp_id, month)
    
    # Calculate salary (without saving)
    payroll = Payroll()
    salary_data = payroll.calculate_salary(emp_id, month)
    
    print(f"\n{'='*60}")
    print(f"SALARY CHECK: {emp_id} - {employee['name']}")
    print(f"{'='*60}")
    print(f"Month: {month}")
    print(f"Base Salary: ₹{employee['base_salary']:,.2f}")
    print(f"Days Present: {days_present}/{salary_data['total_days'] if salary_data else 0}")
    if salary_data:
        print(f"Earned Salary: ₹{salary_data['gross_salary'] - salary_data['hra'] - salary_data['bonus']:,.2f}")
        print(f"HRA: ₹{salary_data['hra']:,.2f}")
        print(f"Bonus: ₹{salary_data['bonus']:,.2f}")
        print(f"Gross: ₹{salary_data['gross_salary']:,.2f}")
        print(f"EPF: -₹{salary_data['epf_deduction']:,.2f}")
        print(f"TDS: -₹{salary_data['tds_deduction']:,.2f}")
        print(f"NET SALARY: ₹{salary_data['net_salary']:,.2f}")
    print(f"{'='*60}\n")
    
    return render_template('admin_check_salary.html',
                         employee=employee,
                         salary_data=salary_data,
                         attendance_records=attendance_records,
                         days_present=days_present,
                         month=month)

@app.route('/admin/payroll')
@login_required
@admin_required
def admin_payroll():
    month = request.args.get('month', get_current_month())
    emp = Employee()
    connection = emp.db.get_connection()
    payroll_records = []
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, e.name, e.department FROM payroll p
            JOIN employees e ON p.emp_id = e.emp_id
            WHERE p.month = %s ORDER BY p.trans_id DESC
        """, (month,))
        payroll_records = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('admin_payroll.html', records=payroll_records, month=month)

@app.route('/download-payslip/<int:trans_id>')
@login_required
def download_payslip(trans_id):
    payroll = Payroll()
    connection = payroll.db.get_connection()
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payroll WHERE trans_id = %s", (trans_id,))
        record = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if record and record['pdf_path']:
            if record['emp_id'] == session['emp_id'] or session.get('role') == 'admin':
                if os.path.exists(record['pdf_path']):
                    return send_file(record['pdf_path'], as_attachment=True)
        flash('Payslip not found!', 'error')
    
    return redirect(url_for('employee_payslips'))

@app.route('/admin/backup')
@login_required
@admin_required
def admin_backup():
    if BackupManager.full_backup():
        log_admin_action('system_backup', 'Created backup')
        flash('Backup completed!', 'success')
    else:
        flash('Backup failed!', 'error')
    return redirect(url_for('admin_dashboard'))

# ======================== RUN APP ========================

if __name__ == '__main__':
    print("\n🔧 Initializing database...")
    db = Database()
    db.create_database_and_tables()
    
    print("\n🚀 Starting Application...")
    print("📍 Access at: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)