"""
Fix Admin Password - Direct Solution
"""

import mysql.connector
import hashlib

print("\n" + "="*70)
print("🔧 FIXING ADMIN PASSWORD")
print("="*70)

# Database connection
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='@Arpit9455',  # YOUR MySQL PASSWORD (blank for most XAMPP)
        database='advanced_payroll'
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Admin details
    email = 'admin@payroll.com'
    password = 'admin123'
    
    # Create BOTH password hashes (bcrypt will be tried first by app.py)
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"\n📋 Creating/Updating Admin:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   SHA256 Hash: {sha256_hash}")
    
    # Check if admin exists
    cursor.execute("SELECT * FROM employees WHERE email = %s", (email,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"\n✅ Admin found: {existing['emp_id']}")
        print(f"   Updating password...")
        
        # Update password
        cursor.execute(
            "UPDATE employees SET password_hash = %s WHERE email = %s",
            (sha256_hash, email)
        )
        conn.commit()
        
        print(f"✅ Password updated!")
        
    else:
        print(f"\n⚠️  Admin not found. Creating new admin...")
        
        # Create admin
        query = """
            INSERT INTO employees 
            (emp_id, name, email, password_hash, department, designation, 
             base_salary, role, status, joining_date, otp_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), TRUE)
        """
        
        cursor.execute(query, (
            'ADMIN001',
            'System Administrator',
            email,
            sha256_hash,
            'Administration',
            'System Admin',
            100000.00,
            'admin',
            'Active'
        ))
        
        conn.commit()
        print(f"✅ Admin created!")
    
    # Verify
    cursor.execute("SELECT emp_id, email, password_hash FROM employees WHERE email = %s", (email,))
    admin = cursor.fetchone()
    
    print("\n" + "="*70)
    print("✅ ADMIN READY!")
    print("="*70)
    print(f"📧 Email:    {email}")
    print(f"🔒 Password: {password}")
    print(f"👤 Emp ID:   {admin['emp_id']}")
    print(f"🔑 Hash:     {admin['password_hash']}")
    print("="*70)
    
    # Test password verification
    print("\n🧪 Testing password verification...")
    test_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if test_hash == admin['password_hash']:
        print("✅ PASSWORD VERIFICATION: SUCCESS!")
        print("\n🎉 You can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
    else:
        print("❌ PASSWORD VERIFICATION: FAILED!")
        print(f"   Expected: {test_hash}")
        print(f"   Got:      {admin['password_hash']}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Done! Now try logging in.\n")

except mysql.connector.Error as e:
    print(f"\n❌ DATABASE ERROR: {e}")
    print("\n💡 Solutions:")
    print("   1. Make sure MySQL is running in XAMPP")
    print("   2. Check database password in this script")
    print("   3. Verify database 'advanced_payroll' exists\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}\n")