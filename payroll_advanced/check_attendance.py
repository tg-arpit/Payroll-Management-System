"""
Check if attendance is being saved in database
"""

import mysql.connector
from datetime import date

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='@Arpit9455',
    database='advanced_payroll'
)

cursor = conn.cursor(dictionary=True)

# Check all attendance records
cursor.execute("SELECT * FROM attendance ORDER BY date DESC LIMIT 10")
records = cursor.fetchall()

print("\n" + "="*60)
print("📋 RECENT ATTENDANCE RECORDS:")
print("="*60)

if records:
    for record in records:
        print(f"\nEmp ID: {record['emp_id']}")
        print(f"Date: {record['date']}")
        print(f"Status: {record['status']}")
        print(f"Check In: {record['check_in_time']}")
        print(f"Check Out: {record['check_out_time']}")
        print("-" * 60)
else:
    print("\n❌ NO ATTENDANCE RECORDS FOUND!")

cursor.close()
conn.close()