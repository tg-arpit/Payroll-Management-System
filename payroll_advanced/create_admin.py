"""
Create the first admin account
"""

from models import Employee
from datetime import date

def create_admin():
    print("\n🔧 Creating Admin Account...\n")
    
    emp = Employee()
    
    # Admin details
    admin_data = {
        'name': 'Admin User',
        'email': 'admin@payroll.com',
        'phone': '9999999999',
        'department': 'Administration',
        'designation': 'System Administrator',
        'joining_date': date.today(),
        'base_salary': 100000.00,
        'password': 'admin123',  # Change this!
        'role': 'admin'
    }
    
    emp_id = emp.create(admin_data)
    
    if emp_id:
        # Mark as verified
        connection = emp.db.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE employees SET otp_verified = TRUE WHERE emp_id = %s",
                (emp_id,)
            )
            connection.commit()
            cursor.close()
            connection.close()
        
        print("✅ Admin account created successfully!")
        print(f"\n📝 Login Credentials:")
        print(f"   📧 Email: {admin_data['email']}")
        print(f"   🔑 Password: {admin_data['password']}")
        print(f"   🆔 Employee ID: {emp_id}")
        print(f"\n⚠️  Please change the password after first login!")
    else:
        print("❌ Failed to create admin account")

if __name__ == "__main__":
    create_admin()