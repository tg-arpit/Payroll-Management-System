# File: check_database.py

import mysql.connector

try:
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='@Arpit9455'
    )
    
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES LIKE 'advanced_payroll'")
    result = cursor.fetchone()
    
    if result:
        print("✅ Database 'advanced_payroll' exists")
        
        # Check tables
        cursor.execute("USE advanced_payroll")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
            
        # Check employees
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        print(f"\n👥 Total employees: {count}")
        
        if count > 0:
            cursor.execute("SELECT emp_id, name, email, role FROM employees")
            employees = cursor.fetchall()
            print("\n📋 Employee List:")
            for emp in employees:
                print(f"   {emp[0]} | {emp[1]} | {emp[2]} | {emp[3]}")
        
    else:
        print("❌ Database 'advanced_payroll' NOT found!")
        print("\n💡 Solution: Run 'python setup_database.py'")
    
    cursor.close()
    connection.close()
    
except mysql.connector.Error as e:
    print(f"❌ Error: {e}")
    print("\n💡 Make sure MySQL is running in XAMPP!")