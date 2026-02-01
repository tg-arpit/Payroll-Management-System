"""
Comprehensive Payroll System Diagnostic and Fix Script
This script will:
1. Check database connection
2. Verify employees exist
3. Check attendance records
4. Test payroll calculation
5. Fix any issues found
"""

import mysql.connector
from datetime import datetime, date, timedelta
from calendar import monthrange
import random

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Arpit9455',
    'database': 'advanced_payroll'
}

def get_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def check_database():
    """Check if database and tables exist"""
    print("\n" + "="*60)
    print("STEP 1: CHECKING DATABASE")
    print("="*60)
    
    conn = get_connection()
    if not conn:
        print("❌ Cannot connect to database!")
        return False
    
    cursor = conn.cursor()
    
    # Check tables
    tables = ['employees', 'attendance', 'payroll']
    for table in tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing!")
            cursor.close()
            conn.close()
            return False
    
    cursor.close()
    conn.close()
    print("✅ Database structure OK")
    return True

def check_employees():
    """Check if employees exist"""
    print("\n" + "="*60)
    print("STEP 2: CHECKING EMPLOYEES")
    print("="*60)
    
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT emp_id, name, base_salary, status, role FROM employees")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not employees:
        print("❌ No employees found!")
        return []
    
    print(f"✅ Found {len(employees)} employees:")
    for emp in employees:
        print(f"   • {emp['emp_id']} - {emp['name']} (Salary: ₹{emp['base_salary']}, Role: {emp['role']}, Status: {emp['status']})")
    
    return employees

def check_attendance(month=None):
    """Check attendance records"""
    print("\n" + "="*60)
    print("STEP 3: CHECKING ATTENDANCE")
    print("="*60)
    
    if month is None:
        month = date.today().strftime('%Y-%m')
    
    print(f"Checking for month: {month}")
    
    conn = get_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all attendance for the month
    query = """
        SELECT emp_id, COUNT(*) as count, 
               SUM(CASE WHEN status = 'Present' THEN 1 
                        WHEN status = 'Half-Day' THEN 0.5 
                        ELSE 0 END) as days_present
        FROM attendance
        WHERE DATE_FORMAT(date, '%Y-%m') = %s
        GROUP BY emp_id
    """
    cursor.execute(query, (month,))
    attendance_summary = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not attendance_summary:
        print(f"❌ No attendance records found for {month}!")
        return {}
    
    attendance_dict = {}
    print(f"✅ Attendance records found:")
    for att in attendance_summary:
        attendance_dict[att['emp_id']] = att['days_present']
        print(f"   • {att['emp_id']}: {att['days_present']} days present (Total records: {att['count']})")
    
    return attendance_dict

def add_sample_attendance(employees, month=None):
    """Add sample attendance data for testing"""
    print("\n" + "="*60)
    print("STEP 4: ADDING SAMPLE ATTENDANCE DATA")
    print("="*60)
    
    if month is None:
        month = date.today().strftime('%Y-%m')
    
    year, mon = map(int, month.split('-'))
    total_days = monthrange(year, mon)[1]
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    for emp in employees:
        emp_id = emp['emp_id']
        
        # Add attendance for each day of the month
        for day in range(1, total_days + 1):
            try:
                attendance_date = date(year, mon, day)
                
                # Skip weekends (Saturday=5, Sunday=6)
                if attendance_date.weekday() >= 5:
                    continue
                
                # 90% chance of Present, 5% Half-Day, 5% Absent
                rand = random.random()
                if rand < 0.90:
                    status = 'Present'
                    check_in = '09:00:00'
                    check_out = '18:00:00'
                elif rand < 0.95:
                    status = 'Half-Day'
                    check_in = '09:00:00'
                    check_out = '13:00:00'
                else:
                    status = 'Absent'
                    check_in = None
                    check_out = None
                
                # Insert attendance
                query = """
                    INSERT INTO attendance (emp_id, date, status, check_in_time, check_out_time, remarks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        status = VALUES(status),
                        check_in_time = VALUES(check_in_time),
                        check_out_time = VALUES(check_out_time)
                """
                cursor.execute(query, (emp_id, attendance_date, status, check_in, check_out, f'Auto-generated for {month}'))
                
            except Exception as e:
                print(f"   ⚠️  Error adding attendance for {emp_id} on {attendance_date}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Added attendance for {emp_id}")
    
    cursor.close()
    conn.close()
    print(f"✅ Sample attendance added for {len(employees)} employees")
    return True

def test_payroll_calculation(emp_id, month):
    """Test payroll calculation for one employee"""
    print("\n" + "="*60)
    print("STEP 5: TESTING PAYROLL CALCULATION")
    print("="*60)
    print(f"Testing for {emp_id}, Month: {month}")
    
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    
    # Get employee
    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
    emp = cursor.fetchone()
    
    if not emp:
        print(f"❌ Employee {emp_id} not found!")
        cursor.close()
        conn.close()
        return None
    
    print(f"✅ Employee: {emp['name']}, Base Salary: ₹{emp['base_salary']}")
    
    # Get attendance
    query = """
        SELECT SUM(CASE 
            WHEN status = 'Present' THEN 1
            WHEN status = 'Half-Day' THEN 0.5
            ELSE 0
        END) as days_present
        FROM attendance
        WHERE emp_id = %s AND DATE_FORMAT(date, '%Y-%m') = %s
    """
    cursor.execute(query, (emp_id, month))
    result = cursor.fetchone()
    days_present = float(result['days_present'] or 0)
    
    print(f"✅ Days Present: {days_present}")
    
    # Calculate salary
    base_salary = float(emp['base_salary'])
    year, mon = map(int, month.split('-'))
    total_days = monthrange(year, mon)[1]
    
    per_day_salary = base_salary / total_days
    earned_salary = per_day_salary * days_present
    
    epf = base_salary * 0.12
    annual_salary = base_salary * 12
    
    if annual_salary <= 250000:
        tds = 0
    elif annual_salary <= 500000:
        tds = (annual_salary - 250000) * 0.05 / 12
    elif annual_salary <= 1000000:
        tds = (12500 + (annual_salary - 500000) * 0.20) / 12
    else:
        tds = (112500 + (annual_salary - 1000000) * 0.30) / 12
    
    lop = (total_days - days_present) * per_day_salary
    hra = base_salary * 0.40
    bonus = base_salary * 0.05
    gross = earned_salary + hra + bonus
    net = gross - epf - tds - lop
    
    salary_data = {
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
    
    print("\n📊 SALARY BREAKDOWN:")
    print(f"   Base Salary: ₹{base_salary:,.2f}")
    print(f"   Days Present: {days_present}/{total_days}")
    print(f"   Earned Salary: ₹{earned_salary:,.2f}")
    print(f"   HRA: +₹{hra:,.2f}")
    print(f"   Bonus: +₹{bonus:,.2f}")
    print(f"   Gross Salary: ₹{gross:,.2f}")
    print(f"   EPF: -₹{epf:,.2f}")
    print(f"   TDS: -₹{tds:,.2f}")
    print(f"   LOP: -₹{lop:,.2f}")
    print(f"   NET SALARY: ₹{net:,.2f}")
    
    cursor.close()
    conn.close()
    
    return salary_data

def process_payroll_for_month(month=None):
    """Process payroll for all employees"""
    print("\n" + "="*60)
    print("STEP 6: PROCESSING PAYROLL")
    print("="*60)
    
    if month is None:
        month = date.today().strftime('%Y-%m')
    
    print(f"Processing payroll for {month}")
    
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all active employees
    cursor.execute("SELECT * FROM employees WHERE status = 'Active'")
    employees = cursor.fetchall()
    
    if not employees:
        print("❌ No active employees found!")
        cursor.close()
        conn.close()
        return 0
    
    success_count = 0
    
    for emp in employees:
        emp_id = emp['emp_id']
        
        # Check if payroll already processed
        cursor.execute("SELECT COUNT(*) as count FROM payroll WHERE emp_id = %s AND month = %s", (emp_id, month))
        existing = cursor.fetchone()
        if existing['count'] > 0:
            print(f"⏭️  Payroll already processed for {emp_id}")
            continue
        
        # Calculate salary
        salary_data = test_payroll_calculation(emp_id, month)
        
        if salary_data and salary_data['days_present'] > 0:
            # Save to database
            try:
                query = """
                    INSERT INTO payroll 
                    (emp_id, month, base_salary, days_present, total_days,
                     epf_deduction, tds_deduction, lop_deduction, hra, bonus,
                     gross_salary, net_salary, payment_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    salary_data['emp_id'], salary_data['month'],
                    salary_data['base_salary'], salary_data['days_present'],
                    salary_data['total_days'], salary_data['epf_deduction'],
                    salary_data['tds_deduction'], salary_data['lop_deduction'],
                    salary_data['hra'], salary_data['bonus'],
                    salary_data['gross_salary'], salary_data['net_salary'],
                    datetime.now().date(), 'Processed'
                )
                cursor.execute(query, values)
                conn.commit()
                success_count += 1
                print(f"✅ Payroll saved for {emp_id}")
            except Exception as e:
                print(f"❌ Error saving payroll for {emp_id}: {e}")
        else:
            print(f"⚠️  No attendance data for {emp_id}")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ PAYROLL PROCESSING COMPLETE!")
    print(f"   Successfully processed: {success_count}/{len(employees)} employees")
    
    return success_count

def main():
    """Main diagnostic and fix routine"""
    print("\n" + "="*60)
    print("PAYROLL SYSTEM DIAGNOSTIC AND FIX")
    print("="*60)
    
    # Step 1: Check database
    if not check_database():
        print("\n❌ Database structure issues found. Please run setup_database.py first.")
        return
    
    # Step 2: Check employees
    employees = check_employees()
    if not employees:
        print("\n❌ No employees found. Please add employees first.")
        print("   You can use the web interface to register employees.")
        return
    
    # Step 3: Check attendance
    current_month = date.today().strftime('%Y-%m')
    attendance = check_attendance(current_month)
    
    # Step 4: Add sample attendance if missing
    if not attendance:
        print("\n⚠️  No attendance records found!")
        response = input("Would you like to add sample attendance data? (yes/no): ")
        if response.lower() == 'yes':
            add_sample_attendance(employees, current_month)
            attendance = check_attendance(current_month)
    
    # Step 5: Test calculation for first employee
    if employees and attendance:
        first_emp = employees[0]['emp_id']
        test_payroll_calculation(first_emp, current_month)
    
    # Step 6: Process payroll
    print("\n" + "="*60)
    response = input("Would you like to process payroll now? (yes/no): ")
    if response.lower() == 'yes':
        success_count = process_payroll_for_month(current_month)
        print(f"\n✅ DONE! Processed payroll for {success_count} employees")
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the Flask application: python app.py")
    print("2. Navigate to: http://localhost:5000/admin/payroll")
    print("3. You should now see payroll records!")
    print("="*60)

if __name__ == '__main__':
    main()
