"""
❓ WHY THIS FILE EXISTS:
This is a utility 'Wrapper'. Instead of calling Razorpay's broad library everywhere, 
we create a clean interface here for specifically what our app needs: 
Creating Orders and Verifying Signatures.
"""
import razorpay
from django.conf import settings

class RazorpayClient:
    """Razorpay client wrapper"""
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount, currency="INR", receipt="receipt"):
        """
        💳 HOW: Order Creation
        Razorpay needs to know the Amount and receipt ID before a user can pay.
        Wait... why use 'receipt'? It helps us reconcile payments in the dashboard later.
        """
        data = {
            "amount": int(amount * 100),  # Razorpay expects amount in paise
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1  # Auto capture payment
        }
        
        try:
            order = self.client.order.create(data=data)
            return {
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'receipt': order['receipt']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        🔐 WHY: Security (Mandatory)
        This ensures that the payment data received on the success page hasn't 
        been tampered with. It protects against hackers faking successful payments.
        """
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except:
            return False
    
    def fetch_payment(self, payment_id):
        """Fetch payment details"""
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except:
            return None

# Create global instance
razorpay_client = RazorpayClient()