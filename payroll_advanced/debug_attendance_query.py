"""
DEBUG - Test Attendance Query
Run this to see what Flask is actually getting
"""

import mysql.connector

print("\n🔍 TESTING ATTENDANCE QUERIES")
print("="*70)

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='@Arpit9455',
    database='advanced_payroll'
)

cursor = conn.cursor(dictionary=True)

# Test month
month = '2026-01'

print(f"\n📅 Testing for month: {month}\n")

# Get employees
cursor.execute("SELECT emp_id, name FROM employees ORDER BY emp_id")
employees = cursor.fetchall()

print(f"Found {len(employees)} employees:\n")

for emp in employees:
    emp_id = emp['emp_id']
    name = emp['name']
    
    print(f"{'='*70}")
    print(f"Employee: {emp_id} - {name}")
    print(f"{'='*70}")
    
    # Test 1: Get monthly records
    query1 = """
        SELECT * FROM attendance 
        WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
        ORDER BY date DESC
    """
    cursor.execute(query1, (emp_id, '%Y-%m', month))
    records = cursor.fetchall()
    
    print(f"\n1. Get Monthly Records:")
    print(f"   Query: WHERE emp_id = '{emp_id}' AND DATE_FORMAT(date, '%Y-%m') = '{month}'")
    print(f"   Found: {len(records)} records")
    
    if records:
        print(f"\n   Sample records:")
        for r in records[:5]:
            print(f"   - {r['date']} | {r['status']}")
    
    # Test 2: Calculate days present
    query2 = """
        SELECT 
            SUM(CASE 
                WHEN status = 'Half-Day' THEN 0.5 
                WHEN status = 'Present' THEN 1 
                ELSE 0 
            END) as effective_days
        FROM attendance 
        WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
    """
    cursor.execute(query2, (emp_id, '%Y-%m', month))
    result = cursor.fetchone()
    
    days = float(result['effective_days']) if result['effective_days'] else 0
    
    print(f"\n2. Calculate Days Present:")
    print(f"   Effective days: {days}")
    
    # Test 3: Manual count
    query3 = """
        SELECT status, COUNT(*) as count
        FROM attendance 
        WHERE emp_id = %s AND DATE_FORMAT(date, %s) = %s
        GROUP BY status
    """
    cursor.execute(query3, (emp_id, '%Y-%m', month))
    breakdown = cursor.fetchall()
    
    print(f"\n3. Status Breakdown:")
    for b in breakdown:
        print(f"   {b['status']}: {b['count']} days")
    
    print(f"\n")

cursor.close()
conn.close()

print("="*70)
print("✅ TEST COMPLETE")
print("="*70)
print("\n💡 If Flask shows different results, there's a bug in the code!\n")