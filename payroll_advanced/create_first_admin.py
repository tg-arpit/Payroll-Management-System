"""
Create First Admin Account
"""

import mysql.connector
import hashlib
from datetime import date

print("\n🔧 Creating Admin Account...")

# Database connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='@Arpit9455',  # YOUR MySQL PASSWORD
    database='advanced_payroll'
)

cursor = conn.cursor()

# Admin details
admin_data = {
    'emp_id': 'ADMIN001',
    'name': 'System Administrator',
    'email': 'admin@payroll.com',
    'password': 'admin123',
    'department': 'Administration',
    'designation': 'System Admin',
    'base_salary': 100000.00,
    'role': 'admin'
}

# Hash password
password_hash = hashlib.sha256(admin_data['password'].encode()).hexdigest()

# Check if admin exists
cursor.execute("SELECT * FROM employees WHERE email = %s", (admin_data['email'],))
existing = cursor.fetchone()

if existing:
    print("⚠️  Admin already exists!")
    print(f"   Email: {admin_data['email']}")
else:
    # Create admin
    query = """
        INSERT INTO employees 
        (emp_id, name, email, password_hash, department, designation, base_salary, role, status, joining_date, otp_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s, TRUE)
    """
    
    cursor.execute(query, (
        admin_data['emp_id'],
        admin_data['name'],
        admin_data['email'],
        password_hash,
        admin_data['department'],
        admin_data['designation'],
        admin_data['base_salary'],
        admin_data['role'],
        date.today()
    ))
    
    conn.commit()
    
    print("\n✅ Admin Account Created Successfully!")
    print("="*50)
    print(f"Employee ID: {admin_data['emp_id']}")
    print(f"Email: {admin_data['email']}")
    print(f"Password: {admin_data['password']}")
    print("="*50)
    print("\n⚠️  IMPORTANT: Change password after first login!\n")

cursor.close()
conn.close()