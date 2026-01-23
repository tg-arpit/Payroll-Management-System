"""
Quick Admin Account Creation
"""

import mysql.connector
import bcrypt
from datetime import date

def create_admin():
    print("\n🔧 Creating Admin Account...\n")
    
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='@Arpit8161',  # Your MySQL password
            database='advanced_payroll'
        )
        
        cursor = connection.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT * FROM employees WHERE email = 'admin@payroll.com'")
        existing = cursor.fetchone()
        
        if existing:
            print("⚠️ Admin already exists! Updating password...\n")
            
            # Update password
            password = 'admin123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(
                "UPDATE employees SET password_hash = %s, otp_verified = TRUE WHERE email = 'admin@payroll.com'",
                (password_hash,)
            )
            connection.commit()
            
            print("✅ Admin password updated!")
            
        else:
            print("Creating new admin account...\n")
            
            # Generate employee ID
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            emp_id = f"EMP{str(count + 1).zfill(3)}"
            
            # Hash password
            password = 'admin123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert admin
            query = """
                INSERT INTO employees 
                (emp_id, name, email, password_hash, phone, department, 
                 designation, joining_date, base_salary, role, otp_verified, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                emp_id,
                'Admin User',
                'admin@payroll.com',
                password_hash,
                '9999999999',
                'Administration',
                'System Administrator',
                date.today(),
                100000.00,
                'admin',
                True,
                'Active'
            )
            
            cursor.execute(query, values)
            connection.commit()
            
            print("✅ Admin account created successfully!")
            print(f"   Employee ID: {emp_id}")
        
        print("\n" + "="*60)
        print("📝 LOGIN CREDENTIALS:")
        print("="*60)
        print("   📧 Email: admin@payroll.com")
        print("   🔑 Password: admin123")
        print("="*60)
        print("\n⚠️  Login now at: http://localhost:5000/login\n")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Database Error: {e}")
        print("\n💡 Solutions:")
        print("   1. Make sure MySQL is running in XAMPP")
        print("   2. Make sure database 'advanced_payroll' exists")
        print("   3. Run: python setup_database.py first")

if __name__ == "__main__":
    create_admin()