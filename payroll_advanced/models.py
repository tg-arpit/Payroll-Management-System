"""
Advanced Payroll System - Database Models
Includes: Employees, Attendance, Payroll, Admin Logs
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import bcrypt
from calendar import monthrange

class Database:
    """Database connection handler"""
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = '@Arpit9455'
        self.database = 'advanced_payroll'
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return connection
        except Error as e:
            print(f"❌ Database Error: {e}")
            return None

    def create_database_and_tables(self):
        """Initialize database and all tables"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"✓ Database '{self.database}' created")
            cursor.execute(f"USE {self.database}")
            
            # 1. Employees Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    emp_id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    phone VARCHAR(15),
                    department VARCHAR(50),
                    designation VARCHAR(50),
                    joining_date DATE,
                    base_salary DECIMAL(10, 2) NOT NULL,
                    role ENUM('admin', 'employee') DEFAULT 'employee',
                    status ENUM('Active', 'Inactive') DEFAULT 'Active',
                    otp_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            print("✓ Table 'employees' created")
            
            # 2. Attendance Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    emp_id VARCHAR(20),
                    date DATE NOT NULL,
                    status ENUM('Present', 'Absent', 'Leave', 'Half-Day') NOT NULL,
                    check_in_time TIME,
                    check_out_time TIME,
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_attendance (emp_id, date)
                )
            """)
            print("✓ Table 'attendance' created")
            
            # 3. Payroll Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payroll (
                    trans_id INT AUTO_INCREMENT PRIMARY KEY,
                    emp_id VARCHAR(20),
                    month VARCHAR(7) NOT NULL,
                    base_salary DECIMAL(10, 2),
                    days_present DECIMAL(5, 2),
                    total_days INT,
                    epf_deduction DECIMAL(10, 2) DEFAULT 0,
                    tds_deduction DECIMAL(10, 2) DEFAULT 0,
                    lop_deduction DECIMAL(10, 2) DEFAULT 0,
                    hra DECIMAL(10, 2) DEFAULT 0,
                    bonus DECIMAL(10, 2) DEFAULT 0,
                    gross_salary DECIMAL(10, 2),
                    net_salary DECIMAL(10, 2),
                    pdf_path VARCHAR(255),
                    payment_date DATE,
                    status ENUM('Pending', 'Processed', 'Paid') DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
                )
            """)
            print("✓ Table 'payroll' created")
            
            # 4. Admin Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_id VARCHAR(20),
                    action_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    ip_address VARCHAR(45),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES employees(emp_id) ON DELETE SET NULL
                )
            """)
            print("✓ Table 'admin_logs' created")
            
            # 5. OTP Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS otp_verification (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    purpose ENUM('registration', 'login', 'password_reset') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    verified BOOLEAN DEFAULT FALSE
                )
            """)
            print("✓ Table 'otp_verification' created")
            
            # 6. Leave Requests Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    emp_id VARCHAR(20),
                    leave_type ENUM('Sick', 'Casual', 'Earned') NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    reason TEXT,
                    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
                    approved_by VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
                    FOREIGN KEY (approved_by) REFERENCES employees(emp_id) ON DELETE SET NULL
                )
            """)
            print("✓ Table 'leave_requests' created")
            
            connection.commit()
            print("\n✅ All tables created successfully!")
            cursor.close()
            connection.close()
            
        except Error as e:
            print(f"❌ Error creating tables: {e}")


class Employee:
    """Employee Model"""
    
    def __init__(self):
        self.db = Database()
    
    def generate_emp_id(self):
        """Generate unique employee ID (EMP001)"""
        connection = self.db.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return f"EMP{str(count + 1).zfill(3)}"
        return "EMP001"
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create(self, data):
        """Create new employee"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                emp_id = data.get('emp_id', self.generate_emp_id())
                password_hash = self.hash_password(data['password'])
                
                query = """
                    INSERT INTO employees 
                    (emp_id, name, email, password_hash, phone, department, 
                     designation, joining_date, base_salary, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    emp_id, data['name'], data['email'], password_hash,
                    data.get('phone'), data.get('department'),
                    data.get('designation'), data.get('joining_date'),
                    data['base_salary'], data.get('role', 'employee')
                )
                
                cursor.execute(query, values)
                connection.commit()
                cursor.close()
                connection.close()
                return emp_id
            except Error as e:
                print(f"❌ Error: {e}")
                return None
        return None
    
    def get_by_email(self, email):
        """Get employee by email"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM employees WHERE email = %s", (email,))
                employee = cursor.fetchone()
                cursor.close()
                connection.close()
                return employee
            except Error as e:
                print(f"❌ Error: {e}")
                return None
        return None
    
    def get_by_id(self, emp_id):
        """Get employee by ID"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
                employee = cursor.fetchone()
                cursor.close()
                connection.close()
                return employee
            except Error as e:
                return None
        return None
    
    def get_all(self, include_inactive=False):
        """Get all employees"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                if include_inactive:
                    cursor.execute("SELECT * FROM employees ORDER BY emp_id")
                else:
                    cursor.execute("SELECT * FROM employees WHERE status = 'Active' ORDER BY emp_id")
                employees = cursor.fetchall()
                cursor.close()
                connection.close()
                return employees
            except Error as e:
                return []
        return []
    
    def update_status(self, emp_id, status):
        """Update employee status"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE employees SET status = %s WHERE emp_id = %s",
                    (status, emp_id)
                )
                connection.commit()
                cursor.close()
                connection.close()
                return True
            except Error as e:
                return False
        return False
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
                print(f"❌ Error: {e}")
                return False
        return False
class Attendance:
    """Attendance Model - COMPLETELY FIXED"""
    
    def __init__(self):
        self.db = Database()
    
    def mark(self, emp_id, date, status, check_in=None, check_out=None, remarks=None):
        """Mark attendance with detailed error logging"""
        print(f"\n🔄 ATTENDANCE.MARK() CALLED:")
        print(f"   Emp ID: {emp_id}")
        print(f"   Date: {date}")
        print(f"   Status: {status}")
        print(f"   Check In: {check_in}")
        print(f"   Check Out: {check_out}")
        print(f"   Remarks: {remarks}")
        
        connection = self.db.get_connection()
        if not connection:
            print("❌ DATABASE CONNECTION FAILED!")
            return False
        
        print(f"✅ Database connected")
        
        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO attendance 
                (emp_id, date, status, check_in_time, check_out_time, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                check_in_time = VALUES(check_in_time),
                check_out_time = VALUES(check_out_time),
                remarks = VALUES(remarks)
            """
            
            print(f"🔄 Executing INSERT query...")
            cursor.execute(query, (emp_id, date, status, check_in, check_out, remarks))
            connection.commit()
            
            print(f"✅ ATTENDANCE SAVED TO DATABASE!")
            print(f"   Rows affected: {cursor.rowcount}")
            
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ DATABASE ERROR IN MARK():")
            print(f"   Error: {e}")
            print(f"   Type: {type(e).__name__}")
            if connection:
                connection.close()
            return False
    def get_monthly(self, emp_id, month):
        """Get monthly attendance (YYYY-MM) - WITH DEBUG"""
        print(f"\n🔍 ATTENDANCE.GET_MONTHLY() CALLED:")
        print(f"   Emp ID: {emp_id}")
        print(f"   Month: {month}")
        
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT * FROM attendance 
                    WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
                    ORDER BY date DESC
                """
                cursor.execute(query, (emp_id, '%Y-%m', month))
                records = cursor.fetchall()
                
                print(f"✅ Found {len(records)} records")
                
                cursor.close()
                connection.close()
                return records
            except Exception as e:
                print(f"❌ ERROR in get_monthly(): {e}")
                return []
        else:
            print(f"❌ No database connection")
            return []
    def get_days_present(self, emp_id, month):
        """Calculate days present - COMPLETELY FIXED"""
        print(f"\n🔍 GET_DAYS_PRESENT() CALLED:")
        print(f"   Emp ID: {emp_id}")
        print(f"   Month: {month}")
        
        connection = self.db.get_connection()
        if not connection:
            print("❌ No database connection!")
            return 0.0
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    SUM(CASE 
                        WHEN status = 'Present' THEN 1.0
                        WHEN status = 'Half-Day' THEN 0.5 
                        ELSE 0 
                    END) as effective_days
                FROM attendance 
                WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
            """
            
            print(f"   Executing query...")
            cursor.execute(query, (emp_id, '%Y-%m', month))
            result = cursor.fetchone()
            
            print(f"   Query result: {result}")
            
            cursor.close()
            connection.close()
            
            if result and result['effective_days'] is not None:
                days = float(result['effective_days'])
                print(f"   ✅ Returning: {days} days")
                return days
            else:
                print(f"   ⚠️ No data found, returning 0.0")
                return 0.0
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 0.0
    def get_all_for_month(self, month):
        """Get all attendance for a month"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT a.*, e.name, e.department
                    FROM attendance a
                    JOIN employees e ON a.emp_id = e.emp_id
                    WHERE DATE_FORMAT(a.date, %s) = %s
                    ORDER BY a.date DESC, a.emp_id
                """
                cursor.execute(query, ('%Y-%m', month))
                records = cursor.fetchall()
                cursor.close()
                connection.close()
                return records
            except Exception as e:
                print(f"❌ ERROR in get_all_for_month(): {e}")
                return []
        return []
class Payroll:
    """Payroll Model - Salary Calculations"""
    
    def __init__(self):
        self.db = Database()
        self.employee = Employee()
        self.attendance = Attendance()
    
    def calculate_salary(self, emp_id, month):
        """Calculate salary with deductions"""
        emp = self.employee.get_by_id(emp_id)
        if not emp:
            return None
        
        base_salary = float(emp['base_salary'])
        days_present = self.attendance.get_days_present(emp_id, month)
        
        # Total working days in month
        year, mon = map(int, month.split('-'))
        total_days = monthrange(year, mon)[1]
        
        # Pro-rata salary
        per_day_salary = base_salary / total_days
        earned_salary = per_day_salary * days_present
        
        # EPF: 12% of base
        epf = base_salary * 0.12
        
        # TDS calculation
        annual_salary = base_salary * 12
        if annual_salary <= 250000:
            tds = 0
        elif annual_salary <= 500000:
            tds = (annual_salary - 250000) * 0.05 / 12
        elif annual_salary <= 1000000:
            tds = (12500 + (annual_salary - 500000) * 0.20) / 12
        else:
            tds = (112500 + (annual_salary - 1000000) * 0.30) / 12
        
        # LOP (Loss of Pay)
        lop = (total_days - days_present) * per_day_salary
        
        # HRA: 40% of base for metro cities
        hra = base_salary * 0.40
        
        # Bonus (example: 5% of base)
        bonus = base_salary * 0.05
        
        # Gross Salary
        gross = earned_salary + hra + bonus
        
        # Net Salary
        net = gross - epf - tds - lop
        
        return {
            'emp_id': emp_id,
            'month': month,
            'base_salary': base_salary,
            'days_present': days_present,
            'total_days': total_days,
            'epf_deduction': round(epf, 2),
            'tds_deduction': round(tds, 2),
            'lop_deduction': round(lop, 2),
            'hra': round(hra, 2),
            'bonus': round(bonus, 2),
            'gross_salary': round(gross, 2),
            'net_salary': round(net, 2)
        }
    
    def save_payroll(self, salary_data, pdf_path=None):
        """Save payroll record"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                    INSERT INTO payroll 
                    (emp_id, month, base_salary, days_present, total_days,
                     epf_deduction, tds_deduction, lop_deduction, hra, bonus,
                     gross_salary, net_salary, pdf_path, payment_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    salary_data['emp_id'], salary_data['month'],
                    salary_data['base_salary'], salary_data['days_present'],
                    salary_data['total_days'], salary_data['epf_deduction'],
                    salary_data['tds_deduction'], salary_data['lop_deduction'],
                    salary_data['hra'], salary_data['bonus'],
                    salary_data['gross_salary'], salary_data['net_salary'],
                    pdf_path, datetime.now().date(), 'Processed'
                )
                cursor.execute(query, values)
                connection.commit()
                trans_id = cursor.lastrowid
                cursor.close()
                connection.close()
                return trans_id
            except Error as e:
                print(f"❌ Error: {e}")
                return None
        return None
    
    def get_employee_payslips(self, emp_id):
        """Get all payslips for employee"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT * FROM payroll 
                    WHERE emp_id = %s 
                    ORDER BY month DESC
                """
                cursor.execute(query, (emp_id,))
                payslips = cursor.fetchall()
                cursor.close()
                connection.close()
                return payslips
            except Error as e:
                return []
        return []


class AdminLog:
    """Admin Activity Logging"""
    
    def __init__(self):
        self.db = Database()
    
    def log_action(self, admin_id, action_type, description, ip_address=None):
        """Log admin action"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                    INSERT INTO admin_logs 
                    (admin_id, action_type, description, ip_address)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (admin_id, action_type, description, ip_address))
                connection.commit()
                cursor.close()
                connection.close()
                return True
            except Error as e:
                return False
        return False
    
    def get_logs(self, limit=100):
        """Get recent logs"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT al.*, e.name as admin_name
                    FROM admin_logs al
                    LEFT JOIN employees e ON al.admin_id = e.emp_id
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                logs = cursor.fetchall()
                cursor.close()
                connection.close()
                return logs
            except Error as e:
                return []
        return []


class OTPVerification:
    """OTP Management"""

    def __init__(self):
        self.db = Database()

    def generate_otp(self):
        """Generate 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))

    def save_otp(self, email, otp, purpose):
        """Save OTP to database"""
        connection = self.db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                expires_at = datetime.now() + timedelta(minutes=10)

                query = """
                    INSERT INTO otp_verification 
                    (email, otp, purpose, expires_at)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (email, otp, purpose, expires_at))
                connection.commit()

                cursor.close()
                connection.close()
                return True
            except Error as e:
                print(f"❌ Error saving OTP: {e}")
                return False
        return False

    def verify_otp(self, email, otp_code, purpose):
        """Verify OTP"""
        connection = self.db.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT * FROM otp_verification
                WHERE email = %s 
                  AND otp = %s 
                  AND purpose = %s 
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """

            cursor.execute(query, (email, otp_code, purpose))
            result = cursor.fetchone()

            if result:
                # Delete used OTP
                cursor.execute(
                    "DELETE FROM otp_verification WHERE id = %s",
                    (result['id'],)
                )
                connection.commit()

                cursor.close()
                connection.close()
                return True

            cursor.close()
            connection.close()
            return False

        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return False
