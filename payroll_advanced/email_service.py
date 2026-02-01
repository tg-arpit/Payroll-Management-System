"""
Email Service - Gmail Integration
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

class EmailService:
    """Email service for sending OTP and notifications"""
    
    def __init__(self):
        # Gmail Configuration
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email_address = 'epayrollmanagements@gmail.com'
        self.email_password = 'fvrz jdct jfwh tkjg'  # ← PASTE APP PASSWORD HERE
        self.enabled = True  # Set to True to enable emails
    
    def send_email(self, to_email, subject, body):
        """Send email using Gmail SMTP"""
        if not self.enabled:
            print(f"📧 Email disabled. Would send to {to_email}: {subject}")
            return False
        
        try:
            print(f"\n📧 Sending email to {to_email}...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"ePayroll System <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; }}
                    .otp-box {{ background: white; padding: 20px; text-align: center; 
                               border-radius: 10px; margin: 20px 0; border: 2px dashed #667eea; }}
                    .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; 
                                letter-spacing: 5px; }}
                    .footer {{ background: #333; color: white; padding: 20px; text-align: center; 
                              border-radius: 0 0 10px 10px; font-size: 12px; }}
                    .button {{ background: #667eea; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💼 ePayroll Management System</h1>
                    </div>
                    <div class="content">
                        {body}
                    </div>
                    <div class="footer">
                        <p>© 2026 ePayroll Management System</p>
                        <p>📧 epayrollmanagements@gmail.com</p>
                        <p>This is an automated email. Please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Secure connection
            
            # Login
            server.login(self.email_address, self.email_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"❌ Email authentication failed!")
            print(f"   Check if App Password is correct")
            return False
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    
    def send_otp(self, email, otp_code, purpose='verification'):
        """Send OTP code via email"""
        
        if purpose == 'forgot_password':
            subject = "🔑 Password Reset - ePayroll System"
            body = f"""
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password for ePayroll System.</p>
                <p>Use the verification code below to reset your password:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #666;">Your Verification Code</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">
                        Valid for 10 minutes
                    </p>
                </div>
                
                <p><strong>⚠️ Security Note:</strong></p>
                <ul>
                    <li>Never share this code with anyone</li>
                    <li>Our team will never ask for this code</li>
                    <li>If you didn't request this, please ignore this email</li>
                </ul>
                
                <p>Best regards,<br>ePayroll Team</p>
            """
        else:
            subject = "✅ Verification Code - ePayroll System"
            body = f"""
                <h2>Account Verification</h2>
                <p>Welcome to ePayroll Management System!</p>
                <p>Please verify your email address using the code below:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #666;">Your Verification Code</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">
                        Valid for 10 minutes
                    </p>
                </div>
                
                <p>Enter this code to complete your registration.</p>
                
                <p>Best regards,<br>ePayroll Team</p>
            """
        
        return self.send_email(email, subject, body)
    
    def send_password_reset_success(self, email, emp_name):
        """Send confirmation after password reset"""
        subject = "✅ Password Reset Successful - ePayroll System"
        body = f"""
            <h2>Password Changed Successfully</h2>
            <p>Hello {emp_name},</p>
            <p>Your password has been reset successfully.</p>
            
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #155724;">
                    <strong>✅ Your password has been updated</strong>
                </p>
            </div>
            
            <p>You can now login with your new password.</p>
            
            <p><strong>⚠️ Security Alert:</strong></p>
            <p>If you didn't make this change, please contact the administrator immediately.</p>
            
            <p>Best regards,<br>ePayroll Team</p>
        """
        
        return self.send_email(email, subject, body)
    
    def send_welcome_email(self, email, emp_name, emp_id, temp_password):
        """Send welcome email to new employee"""
        subject = "🎉 Welcome to ePayroll System"
        body = f"""
            <h2>Welcome to ePayroll Management System!</h2>
            <p>Hello {emp_name},</p>
            <p>Your employee account has been created successfully.</p>
            
            <div style="background: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Your Login Credentials:</h3>
                <p><strong>Employee ID:</strong> {emp_id}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Temporary Password:</strong> <code style="background: #fff; padding: 5px 10px; border-radius: 3px;">{temp_password}</code></p>
            </div>
            
            <p><strong>⚠️ Important:</strong> Please change your password after first login.</p>
            
            <a href="http://localhost:5000/login" class="button">Login Now</a>
            
            <p style="margin-top: 30px;">Best regards,<br>ePayroll Team</p>
        """
        
        return self.send_email(email, subject, body)