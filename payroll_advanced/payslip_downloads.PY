"""
PAYSLIP DOWNLOAD FIX - Complete Diagnostic & Repair
====================================================

This script will:
1. Check database records
2. Check if PDF files exist
3. Regenerate missing PDFs
4. Fix download issues
"""

import os
import sys
from models import Database, Employee, Payroll
from utils import PDFGenerator

def diagnose_and_fix():
    """Diagnose and fix payslip issues"""
    
    print("\n" + "="*60)
    print("PAYSLIP DOWNLOAD DIAGNOSTIC")
    print("="*60 + "\n")
    
    # Initialize
    payroll = Payroll()
    pdf_gen = PDFGenerator()
    
    # Get database connection
    connection = payroll.db.get_connection()
    if not connection:
        print("❌ Cannot connect to database!")
        return
    
    cursor = connection.cursor(dictionary=True)
    
    # Check payroll records
    print("📊 Checking payroll records...")
    cursor.execute("SELECT * FROM payroll ORDER BY trans_id DESC LIMIT 10")
    records = cursor.fetchall()
    
    if not records:
        print("❌ No payroll records found!")
        print("\n💡 Solution: Process payroll first!")
        cursor.close()
        connection.close()
        return
    
    print(f"✅ Found {len(records)} payroll records\n")
    
    # Check each record
    print("="*60)
    print("DETAILED CHECK:")
    print("="*60 + "\n")
    
    fixed_count = 0
    missing_pdf_count = 0
    
    for record in records:
        trans_id = record['trans_id']
        emp_id = record['emp_id']
        month = record['month']
        pdf_path = record['pdf_path']
        
        print(f"\n📋 Trans ID: {trans_id}")
        print(f"   Employee: {emp_id}")
        print(f"   Month: {month}")
        print(f"   PDF Path: {pdf_path}")
        
        # Check if PDF exists
        if pdf_path and os.path.exists(pdf_path):
            print(f"   ✅ PDF exists: {pdf_path}")
        else:
            print(f"   ❌ PDF missing!")
            missing_pdf_count += 1
            
            # Try to regenerate PDF
            print(f"   🔧 Attempting to regenerate PDF...")
            
            try:
                # Get employee data
                cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
                employee = cursor.fetchone()
                
                if not employee:
                    print(f"   ❌ Employee not found!")
                    continue
                
                # Prepare salary data
                salary_data = {
                    'emp_id': emp_id,
                    'month': month,
                    'base_salary': float(record['base_salary']),
                    'days_present': float(record['days_present']),
                    'total_days': int(record['total_days']),
                    'hra': float(record['hra']),
                    'bonus': float(record['bonus']),
                    'gross_salary': float(record['gross_salary']),
                    'epf_deduction': float(record['epf_deduction']),
                    'tds_deduction': float(record['tds_deduction']),
                    'lop_deduction': float(record['lop_deduction']),
                    'net_salary': float(record['net_salary'])
                }
                
                # Generate PDF
                pdf_filename = f"{emp_id}_{month}.pdf"
                new_pdf_path = os.path.join('payslips', pdf_filename)
                
                # Make sure payslips directory exists
                os.makedirs('payslips', exist_ok=True)
                
                if pdf_gen.generate_payslip(employee, salary_data, new_pdf_path):
                    # Update database with new path
                    cursor.execute(
                        "UPDATE payroll SET pdf_path = %s WHERE trans_id = %s",
                        (new_pdf_path, trans_id)
                    )
                    connection.commit()
                    
                    print(f"   ✅ PDF regenerated: {new_pdf_path}")
                    fixed_count += 1
                else:
                    print(f"   ❌ Failed to generate PDF")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    cursor.close()
    connection.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total records checked: {len(records)}")
    print(f"PDFs missing: {missing_pdf_count}")
    print(f"PDFs regenerated: {fixed_count}")
    print("="*60 + "\n")
    
    if fixed_count > 0:
        print("✅ PDFs have been regenerated!")
        print("🎉 Try downloading payslips again from employee panel!")
    
    if missing_pdf_count > fixed_count:
        print("\n⚠️  Some PDFs could not be regenerated.")
        print("💡 You may need to re-process payroll for those months.")

if __name__ == "__main__":
    try:
        diagnose_and_fix()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)