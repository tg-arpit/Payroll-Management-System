"""
Utility Functions for Payroll System
PDF generation, Excel handling, Database backup
"""

from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import shutil
import zipfile

class PDFGenerator:
    """Generate professional PDF payslips"""
    
    def __init__(self):
        self.pdf = FPDF()
        self.company_name = "XYZ Corporation"
        self.company_address = "123 Business Park, City, State - 123456"
    
    def generate_payslip(self, employee_data, salary_data, output_path):
        """Generate payslip PDF"""
        try:
            self.pdf.add_page()
            
            # Company Header
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 10, self.company_name, 0, 1, "C")
            self.pdf.set_font("Arial", "", 10)
            self.pdf.cell(0, 5, self.company_address, 0, 1, "C")
            self.pdf.ln(5)
            
            # Payslip Title
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 10, f"SALARY SLIP - {salary_data['month']}", 0, 1, "C")
            self.pdf.ln(5)
            
            # Employee Details
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(50, 8, "Employee ID:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(60, 8, employee_data['emp_id'], 1)
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(40, 8, "Name:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(0, 8, employee_data['name'], 1, 1)
            
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(50, 8, "Department:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(60, 8, employee_data.get('department', 'N/A'), 1)
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(40, 8, "Designation:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(0, 8, employee_data.get('designation', 'N/A'), 1, 1)
            
            self.pdf.ln(5)
            
            # Attendance Summary
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(50, 8, "Days Present:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(60, 8, str(salary_data['days_present']), 1)
            self.pdf.set_font("Arial", "B", 11)
            self.pdf.cell(40, 8, "Total Days:", 1)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.cell(0, 8, str(salary_data['total_days']), 1, 1)
            
            self.pdf.ln(5)
            
            # Earnings
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(95, 8, "EARNINGS", 1, 0, "C")
            self.pdf.cell(95, 8, "DEDUCTIONS", 1, 1, "C")
            
            # Earnings Column
            self.pdf.set_font("Arial", "B", 10)
            self.pdf.cell(65, 7, "Component", 1)
            self.pdf.cell(30, 7, "Amount (Rs.)", 1)
            
            # Deductions Column
            self.pdf.cell(65, 7, "Component", 1)
            self.pdf.cell(30, 7, "Amount (Rs.)", 1, 1)
            
            self.pdf.set_font("Arial", "", 10)
            
            # Row 1
            self.pdf.cell(65, 7, "Basic Salary", 1)
            self.pdf.cell(30, 7, f"{salary_data['base_salary']:,.2f}", 1)
            self.pdf.cell(65, 7, "EPF (12%)", 1)
            self.pdf.cell(30, 7, f"{salary_data['epf_deduction']:,.2f}", 1, 1)
            
            # Row 2
            self.pdf.cell(65, 7, "HRA (40%)", 1)
            self.pdf.cell(30, 7, f"{salary_data['hra']:,.2f}", 1)
            self.pdf.cell(65, 7, "TDS", 1)
            self.pdf.cell(30, 7, f"{salary_data['tds_deduction']:,.2f}", 1, 1)
            
            # Row 3
            self.pdf.cell(65, 7, "Bonus", 1)
            self.pdf.cell(30, 7, f"{salary_data['bonus']:,.2f}", 1)
            self.pdf.cell(65, 7, "LOP", 1)
            self.pdf.cell(30, 7, f"{salary_data['lop_deduction']:,.2f}", 1, 1)
            
            # Totals
            self.pdf.set_font("Arial", "B", 10)
            self.pdf.cell(65, 7, "Gross Salary", 1)
            self.pdf.cell(30, 7, f"{salary_data['gross_salary']:,.2f}", 1)
            self.pdf.cell(65, 7, "Total Deductions", 1)
            total_deductions = (salary_data['epf_deduction'] + 
                              salary_data['tds_deduction'] + 
                              salary_data['lop_deduction'])
            self.pdf.cell(30, 7, f"{total_deductions:,.2f}", 1, 1)
            
            self.pdf.ln(5)
            
            # Net Salary
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(95, 10, "NET SALARY", 1, 0, "C")
            self.pdf.cell(95, 10, f"Rs. {salary_data['net_salary']:,.2f}", 1, 1, "C")
            
            self.pdf.ln(10)
            
            # Footer
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 5, "This is a computer-generated document. No signature required.", 0, 1, "C")
            self.pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", 0, 1, "C")
            
            # Save PDF
            self.pdf.output(output_path)
            print(f"✅ PDF generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            return False


class ExcelHandler:
    """Handle bulk employee uploads via Excel"""
    
    @staticmethod
    def read_employee_excel(file_path):
        """Read employee data from Excel"""
        try:
            df = pd.read_excel(file_path)
            
            # Required columns
            required_cols = ['name', 'email', 'phone', 'department', 
                           'designation', 'joining_date', 'base_salary']
            
            # Check if all required columns exist
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return None, f"Missing columns: {', '.join(missing_cols)}"
            
            # Convert to list of dictionaries
            employees = df.to_dict('records')
            return employees, None
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def export_payroll_report(payroll_data, output_path):
        """Export payroll data to Excel"""
        try:
            df = pd.DataFrame(payroll_data)
            df.to_excel(output_path, index=False)
            print(f"✅ Excel exported: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Excel export error: {e}")
            return False


class BackupManager:
    """Database and file backup manager"""
    
    @staticmethod
    def backup_database(output_dir='backups'):
        """Backup MySQL database to SQL file"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{output_dir}/backup_{timestamp}.sql"
            
            # MySQL dump command
            command = f"mysqldump -u root advanced_payroll > {output_file}"
            os.system(command)
            
            print(f"✅ Database backed up: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return None
    
    @staticmethod
    def backup_payslips(payslips_dir='payslips', output_dir='backups'):
        """Backup payslips folder to ZIP"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{output_dir}/payslips_{timestamp}.zip"
            
            # Create ZIP archive
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(payslips_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, payslips_dir)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Payslips backed up: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return None
    
    @staticmethod
    def full_backup():
        """Complete system backup"""
        db_backup = BackupManager.backup_database()
        payslips_backup = BackupManager.backup_payslips()
        
        if db_backup and payslips_backup:
            print("\n✅ Full backup completed successfully!")
            return True
        return False


def get_current_month():
    """Get current month in YYYY-MM format"""
    return datetime.now().strftime('%Y-%m')


def format_currency(amount):
    """Format number as Indian currency"""
    return f"Rs.{amount:,.2f}"