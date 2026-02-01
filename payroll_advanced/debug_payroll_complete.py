"""
Complete Payroll Diagnostic Script
Run this to find ALL issues
"""

import mysql.connector
from datetime import datetime

print("="*70)
print("🔍 PAYROLL DIAGNOSTIC TOOL")
print("="*70)

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Arpit9455',  # Your password
    'database': 'advanced_payroll'
}

def test_database_connection():
    """Test 1: Database Connection"""
    print("\n[TEST 1] DATABASE CONNECTION")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ PASS: Connected to database successfully")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: Cannot connect to database")
        print(f"   Error: {e}")
        print("   FIX: Start XAMPP MySQL or check password")
        return False

def test_tables_exist():
    """Test 2: Required Tables"""
    print("\n[TEST 2] DATABASE TABLES")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = ['employees', 'attendance', 'payroll', 'admin_logs', 'otp_verification']
        all_exist = True
        
        for table in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if cursor.fetchone():
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' MISSING!")
                all_exist = False
        
        cursor.close()
        conn.close()
        return all_exist
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_employees():
    """Test 3: Active Employees"""
    print("\n[TEST 3] ACTIVE EMPLOYEES")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT emp_id, name, email, status, base_salary 
            FROM employees 
            WHERE status = 'Active'
        """)
        employees = cursor.fetchall()
        
        if len(employees) == 0:
            print("❌ FAIL: NO ACTIVE EMPLOYEES FOUND!")
            print("   FIX: Add employees first via admin panel")
            cursor.close()
            conn.close()
            return False
        
        print(f"✅ PASS: Found {len(employees)} active employee(s)")
        print("\nEmployee Details:")
        for emp in employees:
            print(f"   - {emp['emp_id']}: {emp['name']}")
            print(f"     Email: {emp['email']}")
            print(f"     Salary: ₹{emp['base_salary']}")
            print(f"     Status: {emp['status']}")
            print()
        
        cursor.close()
        conn.close()
        return True, employees
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False, []

def test_attendance(employees):
    """Test 4: Attendance Records"""
    print("\n[TEST 4] ATTENDANCE RECORDS")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Check for current month (2026-01)
        current_month = '2026-01'
        
        all_good = True
        for emp in employees:
            emp_id = emp['emp_id']
            
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                       SUM(CASE WHEN status = 'Half-Day' THEN 1 ELSE 0 END) as halfday
                FROM attendance 
                WHERE emp_id = %s 
                AND DATE_FORMAT(date, %s) = %s
            """, (emp_id, '%Y-%m', current_month))
            
            result = cursor.fetchone()
            total = result['total'] or 0
            present = result['present'] or 0
            halfday = result['halfday'] or 0
            
            if total == 0:
                print(f"❌ {emp['name']} ({emp_id}): NO ATTENDANCE for {current_month}")
                print(f"   FIX: Mark attendance first!")
                all_good = False
            else:
                effective_days = present + (halfday * 0.5)
                print(f"✅ {emp['name']} ({emp_id}): {total} records")
                print(f"   Present: {present}, Half-Day: {halfday}")
                print(f"   Effective Days: {effective_days}")
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_payroll_table_structure():
    """Test 5: Payroll Table Structure"""
    print("\n[TEST 5] PAYROLL TABLE STRUCTURE")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("DESCRIBE payroll")
        columns = cursor.fetchall()
        
        required_columns = [
            'trans_id', 'emp_id', 'month', 'base_salary', 'days_present',
            'total_days', 'epf_deduction', 'tds_deduction', 'lop_deduction',
            'hra', 'bonus', 'gross_salary', 'net_salary', 'pdf_path',
            'payment_date', 'status', 'created_at'
        ]
        
        existing_columns = [col[0] for col in columns]
        
        all_good = True
        for col in required_columns:
            if col in existing_columns:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' MISSING!")
                all_good = False
        
        cursor.close()
        conn.close()
        return all_good
    except Exception as e:
        print(f"❌ FAIL: {e}")
        print("   FIX: Create payroll table")
        return False

def test_folders():
    """Test 6: Required Folders"""
    print("\n[TEST 6] REQUIRED FOLDERS")
    print("-" * 50)
    import os
    
    folders = ['uploads', 'payslips', 'backups', 'logs']
    all_good = True
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"✅ Folder '{folder}' exists")
        else:
            print(f"❌ Folder '{folder}' MISSING!")
            all_good = False
    
    return all_good

def test_fpdf_installed():
    """Test 7: FPDF Library"""
    print("\n[TEST 7] FPDF LIBRARY")
    print("-" * 50)
    try:
        from fpdf import FPDF
        print("✅ PASS: FPDF library installed")
        return True
    except ImportError:
        print("❌ FAIL: FPDF library NOT installed")
        print("   FIX: pip install fpdf")
        return False

def simulate_payroll_calculation(employees):
    """Test 8: Simulate Payroll Calculation"""
    print("\n[TEST 8] PAYROLL CALCULATION SIMULATION")
    print("-" * 50)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        month = '2026-01'
        year, mon = 2026, 1
        from calendar import monthrange
        total_days = monthrange(year, mon)[1]
        
        for emp in employees[:1]:  # Test with first employee
            emp_id = emp['emp_id']
            base_salary = float(emp['base_salary'])
            
            # Get days present
            cursor.execute("""
                SELECT 
                    SUM(CASE 
                        WHEN status = 'Present' THEN 1.0
                        WHEN status = 'Half-Day' THEN 0.5 
                        ELSE 0 
                    END) as effective_days
                FROM attendance 
                WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
            """, (emp_id, '%Y-%m', month))
            
            result = cursor.fetchone()
            days_present = float(result['effective_days'] or 0)
            
            print(f"Testing with: {emp['name']} ({emp_id})")
            print(f"\n📊 CALCULATION BREAKDOWN:")
            print(f"   Base Salary: ₹{base_salary:,.2f}")
            print(f"   Total Days in Month: {total_days}")
            print(f"   Days Present: {days_present}")
            print(f"   Per Day Salary: ₹{base_salary/total_days:,.2f}")
            
            # Calculate components
            per_day = base_salary / total_days
            earned = per_day * days_present
            epf = base_salary * 0.12
            hra = base_salary * 0.40
            bonus = base_salary * 0.05
            lop = (total_days - days_present) * per_day
            
            # TDS calculation
            annual = base_salary * 12
            if annual <= 250000:
                tds = 0
            elif annual <= 500000:
                tds = (annual - 250000) * 0.05 / 12
            else:
                tds = (12500 + (annual - 500000) * 0.20) / 12
            
            gross = earned + hra + bonus
            net = gross - epf - tds - lop
            
            print(f"\n💰 EARNINGS:")
            print(f"   Earned Salary: ₹{earned:,.2f}")
            print(f"   HRA (40%): ₹{hra:,.2f}")
            print(f"   Bonus (5%): ₹{bonus:,.2f}")
            print(f"   GROSS SALARY: ₹{gross:,.2f}")
            
            print(f"\n💳 DEDUCTIONS:")
            print(f"   EPF (12%): ₹{epf:,.2f}")
            print(f"   TDS: ₹{tds:,.2f}")
            print(f"   LOP: ₹{lop:,.2f}")
            print(f"   TOTAL DEDUCTIONS: ₹{(epf+tds+lop):,.2f}")
            
            print(f"\n✅ NET SALARY: ₹{net:,.2f}")
            
            if net <= 0:
                print("\n⚠️ WARNING: Net salary is 0 or negative!")
                print("   Possible reasons:")
                print("   - No attendance marked")
                print("   - Too many deductions")
                return False
            else:
                print("\n✅ Calculation looks good!")
                return True
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run all tests
def main():
    print("\n🚀 Starting comprehensive diagnostics...\n")
    
    results = []
    
    # Test 1: Database
    if not test_database_connection():
        print("\n❌ CRITICAL: Cannot proceed without database connection")
        return
    results.append(True)
    
    # Test 2: Tables
    if not test_tables_exist():
        print("\n❌ CRITICAL: Missing database tables")
        print("   FIX: Run 'python app.py' once to create tables")
        return
    results.append(True)
    
    # Test 3: Employees
    has_employees, employees = test_employees()
    if not has_employees:
        print("\n❌ CRITICAL: No employees to process payroll for")
        return
    results.append(True)
    
    # Test 4: Attendance
    has_attendance = test_attendance(employees)
    results.append(has_attendance)
    
    # Test 5: Payroll Table
    table_ok = test_payroll_table_structure()
    results.append(table_ok)
    
    # Test 6: Folders
    folders_ok = test_folders()
    results.append(folders_ok)
    
    # Test 7: FPDF
    fpdf_ok = test_fpdf_installed()
    results.append(fpdf_ok)
    
    # Test 8: Simulation
    calc_ok = simulate_payroll_calculation(employees)
    results.append(calc_ok)
    
    # Summary
    print("\n" + "="*70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎉 Your payroll system should work!")
        print("\nNext steps:")
        print("   1. Go to admin panel")
        print("   2. Click 'Process Payroll'")
        print("   3. Select month")
        print("   4. Click 'Process Payroll' button")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\nPlease fix the issues marked with ❌ above")
        print("Then run this script again")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()