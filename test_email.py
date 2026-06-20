import os
import django
import sys

# Setup django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_connection():
    print("--- Email Configuration Test ---")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set.")
        print("Please ensure you have saved them in your .env file.")
        return

    recipient = input("\nEnter an email address to send a test email to: ")
    
    if not recipient:
        print("No recipient provided. Exiting.")
        return

    print(f"\nSending test email to {recipient}...")
    
    try:
        send_mail(
            subject="Expense Tracker - Test Email",
            message="Success! Your Django email configuration is working perfectly.\n\nYou are ready to send notifications.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("✅ Email sent successfully! Check your inbox (and spam folder).")
    except Exception as e:
        print("❌ Failed to send email. Error details:")
        print(str(e))

if __name__ == "__main__":
    test_email_connection()
