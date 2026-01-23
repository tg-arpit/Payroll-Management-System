"""
Run this script FIRST to setup the database
"""

from models import Database

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 PAYROLL SYSTEM - DATABASE SETUP")
    print("="*60 + "\n")
    
    db = Database()
    db.create_database_and_tables()
    
    print("\n" + "="*60)
    print("✅ DATABASE SETUP COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Update email credentials in email_service.py")
    print("   2. Run: pip install -r requirements.txt")
    print("   3. Run: python app.py")
    print("   4. Open: http://localhost:5000")
    print("\n" + "="*60 + "\n")