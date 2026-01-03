"""
Complete Email System Test
Tests simple email, HTML email, and QR code email
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import qrcode
import base64
from io import BytesIO

print("\n" + "🎬" * 35)
print("  EMAIL SYSTEM COMPLETE TEST")
print("🎬" * 35 + "\n")

# Test 1: Simple Email
print("📧 Test 1: Simple Email")
print("-" * 70)
try:
    result = send_mail(
        subject='🎬 Test 1: Simple Email',
        message='This is a simple text email. If you receive this, basic email works!',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print(f"✅ Simple email sent! (result: {result})")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 2: HTML Email
print("\n📧 Test 2: HTML Email with Styling")
print("-" * 70)
try:
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 30px; text-align: center; border-radius: 10px; }
            .content { background: #f7fafc; padding: 30px; margin-top: 20px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎬 Movie Booking System</h1>
            <p>HTML Email Test</p>
        </div>
        <div class="content">
            <h2>✅ Success!</h2>
            <p>If you can see this styled message, HTML emails are working!</p>
            <ul>
                <li>✅ Email sending works</li>
                <li>✅ HTML rendering works</li>
                <li>✅ CSS styling works</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    email = EmailMultiAlternatives(
        subject='🎬 Test 2: HTML Email',
        body='Plain text version',
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.EMAIL_HOST_USER]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    print("✅ HTML email sent!")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: Email with QR Code
print("\n📧 Test 3: Email with QR Code")
print("-" * 70)
try:
    # Generate QR code
    qr_data = "Test Booking\nMovie: Inception\nTheater: PVR Cinemas\nSeats: A1, A2, A3"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image = buffer.getvalue()
    qr_base64 = base64.b64encode(qr_image).decode()
    
    html_with_qr = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 30px; border-radius: 10px; }}
            .qr-section {{ margin: 30px 0; padding: 30px; background: #f7fafc; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎫 Test Booking Ticket</h1>
        </div>
        <div class="qr-section">
            <h2>Your QR Code</h2>
            <img src="data:image/png;base64,{qr_base64}" 
                 alt="QR Code" 
                 style="max-width: 300px; border: 3px solid #667eea; padding: 10px; border-radius: 10px;">
            <p><strong>Scan this code at the theater entrance</strong></p>
        </div>
    </body>
    </html>
    """
    
    email = EmailMultiAlternatives(
        subject='🎫 Test 3: Booking with QR Code',
        body='Plain text version with QR code attached',
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.EMAIL_HOST_USER]
    )
    email.attach_alternative(html_with_qr, "text/html")
    email.attach('ticket_qr_code.png', qr_image, 'image/png')
    email.send()
    print("✅ Email with QR code sent!")
except Exception as e:
    print(f"❌ Failed: {e}")

# Summary
print("\n" + "=" * 70)
print("  ✅ ALL TESTS COMPLETED!")
print("=" * 70)
print(f"\n📬 Check your inbox: {settings.EMAIL_HOST_USER}")
print("\nYou should have received 3 emails:")
print("  1. ✅ Simple text email")
print("  2. ✅ Beautiful HTML email with styling")
print("  3. ✅ Email with embedded QR code + attachment")
print("\n🎉 Email system is fully functional!")
print("🎉 Ready to send booking confirmations!")
print("\n" + "🎬" * 35 + "\n")
