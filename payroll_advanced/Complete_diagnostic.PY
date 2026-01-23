"""
Complete Attendance Diagnostic Script
Run this to find the exact problem
"""

import mysql.connector
from datetime import date

print("\n" + "="*70)
print("🔍 COMPLETE ATTENDANCE DIAGNOSTIC")
print("="*70)

# Database credentials
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Arpit9455',  # ← YOUR MySQL PASSWORD
    'database': 'advanced_payroll'
}

try:
    # TEST 1: Database Connection
    print("\n📋 TEST 1: Database Connection")
    print("-"*70)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    print("✅ Connected to database successfully")
    
    cursor = conn.cursor(dictionary=True)
    
    # TEST 2: Check if attendance table exists
    print("\n📋 TEST 2: Attendance Table Structure")
    print("-"*70)
    
    cursor.execute("SHOW TABLES LIKE 'attendance'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("❌ ATTENDANCE TABLE DOES NOT EXIST!")
        print("\n🔧 Creating attendance table...")
        
        cursor.execute("""
            CREATE TABLE attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                status ENUM('Present', 'Absent', 'Leave', 'Half-Day') NOT NULL,
                check_in_time TIME,
                check_out_time TIME,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_attendance (emp_id, date),
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("✅ Attendance table created!")
    else:
        print("✅ Attendance table exists")
        
        # Show structure
        cursor.execute("DESCRIBE attendance")
        columns = cursor.fetchall()
        
        print("\n📊 Table Structure:")
        for col in columns:
            print(f"   {col['Field']:<20} {col['Type']:<25} {col['Null']:<8} {col['Key']}")
    
    # TEST 3: Count records
    print("\n📋 TEST 3: Attendance Records Count")
    print("-"*70)
    
    cursor.execute("SELECT COUNT(*) as total FROM attendance")
    count = cursor.fetchone()['total']
    print(f"Total attendance records: {count}")
    
    # TEST 4: Check employees
    print("\n📋 TEST 4: Available Employees")
    print("-"*70)
    
    cursor.execute("SELECT emp_id, name, email, status, role FROM employees")
    employees = cursor.fetchall()
    
    print(f"Total employees: {len(employees)}")
    for emp in employees:
        print(f"   {emp['emp_id']:<12} {emp['name']:<30} {emp['role']:<10} {emp['status']}")
    
    # TEST 5: Recent attendance records
    if count > 0:
        print("\n📋 TEST 5: Recent Attendance Records")
        print("-"*70)
        
        cursor.execute("""
            SELECT a.*, e.name
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            ORDER BY a.date DESC, a.created_at DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        
        print(f"\nLast {len(recent)} attendance records:")
        for r in recent:
            print(f"   {r['date']} | {r['emp_id']:<12} {r['name']:<25} | {r['status']:<12} | IN: {r['check_in_time'] or 'N/A':<8} OUT: {r['check_out_time'] or 'N/A'}")
    
    # TEST 6: Try inserting test record
    print("\n📋 TEST 6: Test Insert")
    print("-"*70)
    
    if len(employees) > 0:
        test_emp = employees[0]
        test_emp_id = test_emp['emp_id']
        test_date = date.today()
        
        print(f"Testing with: {test_emp_id} ({test_emp['name']})")
        print(f"Date: {test_date}")
        
        # Check if already exists
        cursor.execute(
            "SELECT * FROM attendance WHERE emp_id = %s AND date = %s",
            (test_emp_id, test_date)
        )
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️  Record already exists for today:")
            print(f"   Status: {existing['status']}")
            print(f"   Check-in: {existing['check_in_time']}")
        else:
            print(f"Inserting test record...")
            
            cursor.execute("""
                INSERT INTO attendance 
                (emp_id, date, status, check_in_time, check_out_time, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (test_emp_id, test_date, 'Present', '09:00:00', '18:00:00', 'Test record'))
            
            conn.commit()
            print(f"✅ Test record inserted!")
            
            # Verify
            cursor.execute(
                "SELECT * FROM attendance WHERE emp_id = %s AND date = %s",
                (test_emp_id, test_date)
            )
            inserted = cursor.fetchone()
            
            if inserted:
                print(f"✅ Verified: Record found in database")
                print(f"   ID: {inserted['id']}")
                print(f"   Status: {inserted['status']}")
            else:
                print(f"❌ Verification failed: Record not found!")
    
    # TEST 7: Check month format
    print("\n📋 TEST 7: Month Format Test")
    print("-"*70)
    
    test_month = date.today().strftime('%Y-%m')
    print(f"Current month format: {test_month}")
    
    cursor.execute("""
        SELECT emp_id, date, status
        FROM attendance
        WHERE DATE_FORMAT(date, '%%Y-%%m') = %s
        LIMIT 5
    """, (test_month,))
    
    month_records = cursor.fetchall()
    print(f"Records for {test_month}: {len(month_records)}")
    
    for r in month_records:
        print(f"   {r['date']} | {r['emp_id']} | {r['status']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ DIAGNOSTIC COMPLETE!")
    print("="*70)
    
    if count == 0:
        print("\n⚠️  NO ATTENDANCE RECORDS FOUND!")
        print("   Try marking attendance and run this script again.")
    else:
        print(f"\n✅ Found {count} attendance records in database")
        print("   If attendance not showing in web interface:")
        print("   1. Check browser console for errors")
        print("   2. Clear browser cache (Ctrl+Shift+Delete)")
        print("   3. Check Flask console for errors")
        print("   4. Verify month parameter in URL")
    
    print("\n")

except mysql.connector.Error as e:
    print(f"\n❌ DATABASE ERROR: {e}")
    print(f"   Error Code: {e.errno if hasattr(e, 'errno') else 'N/A'}")
    print("\n💡 Solutions:")
    print("   1. Make sure MySQL is running (XAMPP)")
    print("   2. Check password in DB_CONFIG")
    print("   3. Verify database 'advanced_payroll' exists")
    print("\n")

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    print("\n")