"""
Test Database Connection
"""

import mysql.connector

print("\n🔧 Testing Database Connection")
print("="*60)

try:
    # Connect
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='@Arpit9455',  # YOUR PASSWORD
        database='advanced_payroll'
    )
    
    print("✅ Database connected!")
    
    cursor = conn.cursor(dictionary=True)
    
    # Test 1: Check attendance table
    print("\n1. Checking attendance table...")
    cursor.execute("SHOW TABLES LIKE 'attendance'")
    result = cursor.fetchone()
    
    if result:
        print("   ✅ Attendance table exists")
    else:
        print("   ❌ Attendance table DOES NOT EXIST!")
        print("   Creating table...")
        
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
        print("   ✅ Table created!")
    
    # Test 2: Count records
    print("\n2. Counting records...")
    cursor.execute("SELECT COUNT(*) as total FROM attendance")
    count = cursor.fetchone()['total']
    print(f"   Total records: {count}")
    
    # Test 3: If 0 records, insert test data
    if count == 0:
        print("\n3. No data found! Inserting test records...")
        
        # Get employees
        cursor.execute("SELECT emp_id, name FROM employees")
        employees = cursor.fetchall()
        
        print(f"   Found {len(employees)} employees")
        
        for emp in employees:
            emp_id = emp['emp_id']
            print(f"   Inserting for {emp_id}...")
            
            # Insert 10 days
            for i in range(10):
                cursor.execute("""
                    INSERT INTO attendance 
                    (emp_id, date, status, check_in_time, check_out_time)
                    VALUES (%s, DATE_SUB(CURDATE(), INTERVAL %s DAY), 'Present', '09:00', '18:00')
                    ON DUPLICATE KEY UPDATE status = status
                """, (emp_id, i))
        
        conn.commit()
        
        # Recount
        cursor.execute("SELECT COUNT(*) as total FROM attendance")
        new_count = cursor.fetchone()['total']
        print(f"   ✅ Inserted! New total: {new_count}")
    
    # Test 4: Show sample data
    print("\n4. Sample data:")
    cursor.execute("""
        SELECT a.emp_id, e.name, a.date, a.status
        FROM attendance a
        JOIN employees e ON a.emp_id = e.emp_id
        ORDER BY a.date DESC
        LIMIT 5
    """)
    
    records = cursor.fetchall()
    for r in records:
        print(f"   {r['emp_id']} | {r['name']:<20} | {r['date']} | {r['status']}")
    
    # Test 5: Count by employee
    print("\n5. Count by employee:")
    cursor.execute("""
        SELECT emp_id, COUNT(*) as count 
        FROM attendance 
        GROUP BY emp_id
    """)
    
    counts = cursor.fetchall()
    for c in counts:
        print(f"   {c['emp_id']}: {c['count']} records")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print("\n👉 Now refresh browser: http://127.0.0.1:5000/admin/attendance")
    print("\n")

except mysql.connector.Error as e:
    print(f"\n❌ DATABASE ERROR: {e}")
    print(f"   Code: {e.errno}")
    print("\n💡 Fix:")
    print("   1. Check MySQL is running in XAMPP")
    print("   2. Check password in this script")
    print("   3. Verify database 'advanced_payroll' exists")
    print("\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n")