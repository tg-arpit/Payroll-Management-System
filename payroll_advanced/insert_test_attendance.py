"""
Insert Test Attendance Data
"""

import mysql.connector
from datetime import date, timedelta

print("\n🔧 INSERTING TEST ATTENDANCE DATA")
print("="*70)

# Database connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='@Arpit9455',  # Your password from models.py
    database='advanced_payroll'
)

cursor = conn.cursor(dictionary=True)

# Get employees
cursor.execute("SELECT emp_id, name FROM employees")
employees = cursor.fetchall()

print(f"\n📋 Found {len(employees)} employees:")
for emp in employees:
    print(f"   {emp['emp_id']} - {emp['name']}")

# Insert attendance for last 7 days
print(f"\n🔄 Inserting attendance for last 7 days...")

for emp in employees:
    emp_id = emp['emp_id']
    
    for i in range(7):
        attendance_date = date.today() - timedelta(days=i)
        
        try:
            cursor.execute("""
                INSERT INTO attendance 
                (emp_id, date, status, check_in_time, check_out_time, remarks)
                VALUES (%s, %s, 'Present', '09:00:00', '18:00:00', 'Test data')
                ON DUPLICATE KEY UPDATE status = status
            """, (emp_id, attendance_date))
            
            print(f"   ✅ {emp_id} - {attendance_date}")
        
        except Exception as e:
            print(f"   ❌ {emp_id} - {attendance_date}: {e}")

conn.commit()

# Verify
print(f"\n📊 VERIFICATION:")
cursor.execute("SELECT emp_id, COUNT(*) as count FROM attendance GROUP BY emp_id")
results = cursor.fetchall()

for r in results:
    print(f"   {r['emp_id']}: {r['count']} records")

cursor.close()
conn.close()

print(f"\n✅ DONE! Refresh your browser.\n")