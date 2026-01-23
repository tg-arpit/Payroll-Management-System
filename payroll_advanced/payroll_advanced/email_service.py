"""
Email Service for OTP and Notifications
Uses Gmail SMTP for sending emails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import os

class EmailService:
    """Gmail SMTP Email Service"""
    
    def __init__(self):
        # Gmail SMTP settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # ⚠️ IMPORTANT: Use App Password, not regular Gmail password
        # Generate at: https://myaccount.google.com/apppasswords
        self.sender_email = "epayrollmanagements@gmail.com"  # Change this
        self.sender_password = "fvrzjdctjfwhtkjg"   # Change this
        self.sender_name = "Payroll Management System"
    
    def send_email(self, to_email, subject, body, attachment_path=None):
        """Send email with optional attachment"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype="pdf")
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=os.path.basename(attachment_path)
                    )
                    msg.attach(attachment)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def send_otp(self, to_email, otp, purpose="login"):
        """Send OTP email"""
        subject = f"Your OTP for {purpose.capitalize()}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; }}
                .otp {{ font-size: 32px; font-weight: bold; color: #667eea; text-align: center; padding: 20px; background: #f0f0f0; border-radius: 5px; letter-spacing: 5px; }}
                .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #333;">🔐 OTP Verification</h2>
                <p>Your One-Time Password (OTP) for {purpose} is:</p>
                <div class="otp">{otp}</div>
                <p style="color: #666; margin-top: 20px;">
                    ⏰ This OTP is valid for 10 minutes.<br>
                    ⚠️ Do not share this OTP with anyone.
                </p>
                <div class="footer">
                    <p>© {datetime.now().year} Payroll Management System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body)
    
    def send_registration_success(self, to_email, name, emp_id):
        """Send registration success email"""
        subject = "Welcome to Payroll Management System"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                .emp-id {{ font-size: 24px; font-weight: bold; color: #667eea; padding: 15px; background: #f0f0f0; border-radius: 5px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #667eea;">🎉 Welcome to the Team!</h2>
                <p>Dear {name},</p>
                <p>Your account has been successfully created in our Payroll Management System.</p>
                
                <h3>Your Employee Details:</h3>
                <div class="emp-id">Employee ID: {emp_id}</div>
                
                <p style="margin-top: 20px;">
                    📧 <strong>Login Email:</strong> {to_email}<br>
                    🔑 Use the password you set during registration
                </p>
                
                <p style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    💡 <strong>Important:</strong> Please keep your Employee ID safe. You'll need it for future reference.
                </p>
                
                <p>If you have any questions, please contact HR.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>HR Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body)
    
    def send_payslip(self, to_email, name, month, net_salary, pdf_path):
        """Send monthly payslip"""
        subject = f"Payslip for {month}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                .salary {{ font-size: 28px; font-weight: bold; color: #28a745; text-align: center; padding: 20px; background: #f0fff0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #667eea;">💰 Salary Credited</h2>
                <p>Dear {name},</p>
                <p>Your salary for <strong>{month}</strong> has been processed.</p>
                
                <div class="salary">Net Salary: ₹{net_salary:,.2f}</div>
                
                <p style="margin-top: 20px;">
                    📄 Your detailed payslip is attached to this email as a PDF.<br>
                    💳 The amount has been credited to your registered bank account.
                </p>
                
                <p style="background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    ⚠️ Please verify the details in the attached payslip. Contact HR if you find any discrepancies.
                </p>
                
                <p style="margin-top: 30px;">Best regards,<br>Payroll Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, pdf_path)
    
    def send_password_reset(self, to_email, name, new_password):
        """Send password reset email"""
        subject = "Password Reset Successful"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #667eea;">🔑 Password Reset</h2>
                <p>Dear {name},</p>
                <p>Your password has been successfully reset.</p>
                
                <p style="background: #e7f3ff; padding: 15px; border-radius: 5px;">
                    <strong>New Temporary Password:</strong> {new_password}
                </p>
                
                <p style="color: #dc3545; margin-top: 20px;">
                    ⚠️ <strong>Important Security Notice:</strong><br>
                    - Change this password immediately after login<br>
                    - Don't share this password with anyone<br>
                    - Keep your account secure
                </p>
                
                <p style="margin-top: 30px;">Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body)