"""
❓ WHY THIS FILE EXISTS:
This is a utility 'Wrapper'. Instead of calling Razorpay's broad library everywhere, 
we create a clean interface here for specifically what our app needs: 
Creating Orders and Verifying Signatures.
"""
import time
import razorpay
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RazorpayClient:
    """Razorpay client wrapper"""
    
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_xxxx')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'xxxx')
        
        # 🕵️ Detect Mock Mode:
        # If the keys are placeholders, we enter "Mock Mode" so the user can still 
        # test the app without a real Razorpay account.
        self.is_mock = 'xxxx' in self.key_id or not self.key_secret or self.key_secret == 'xxxx'
        
        if not self.is_mock:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            print("⚠️ WARNING: Running in MOCK PAYMENT MODE. No real transactions will occur.")
    
    def create_order(self, amount, currency="INR", receipt="receipt", notes=None):
        """
        💳 HOW: Order Creation
        WHY: Handshake. We need to register the transaction intent with Razorpay 
        to get a secure 'order_id' that prevents duplicate payments.
        HOW: We convert the amount to 'Paise' (Razorpay standard) and send it with a receipt ID.
        WHEN: Triggers when the user confirms their selection and clicks 'Proceed to pay'.
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            receipt: Receipt ID for tracking
            notes: Optional dictionary of metadata (booking_id, user_id, etc.)
        """
        data = {
            "amount": int(amount * 100),  # Razorpay expects amount in paise
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1  # Auto capture payment
        }
        
        # Add notes if provided
        if notes:
            data["notes"] = notes
        
        if self.is_mock:
            # 🎭 Return a fake order for local testing
            return {
                'success': True,
                'is_mock': True,
                'order_id': f"order_mock_{int(time.time())}",
                'amount': int(amount * 100),
                'currency': currency,
                'receipt': receipt
            }

        # 🔄 RETRY LOGIC: Attempt up to 3 times with exponential backoff
        # This handles transient network errors (connection timeouts, temporary disconnects)
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                order = self.client.order.create(data=data)
                logger.info(f"✅ Razorpay order created successfully: {order['id']}")
                return {
                    'success': True,
                    'is_mock': False,
                    'order_id': order['id'],
                    'amount': order['amount'],
                    'currency': order['currency'],
                    'receipt': order['receipt']
                }
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if retry_count < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** (retry_count - 1)
                    logger.warning(
                        f"⚠️  Razorpay API error (attempt {retry_count}/{max_retries}): {last_error}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"❌ Razorpay API failed after {max_retries} attempts: {last_error}"
                    )
        
        # All retries failed
        return {
            'success': False,
            'error': f"Payment gateway temporarily unavailable. Please try again in a moment. ({last_error})"
        }
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        🔐 WHY: Security (Mandatory)
        This ensures that the payment data received on the success page hasn't 
        been tampered with. It protects against hackers faking successful payments.
        HOW: We use Razorpay's HMAC-SHA256 verification algorithm.
        WHEN: Triggers on the payment_success redirect.
        """
        # Validate inputs - prevent None/empty values
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return False
        
        if self.is_mock:
            # 🎭 WHY: Smooth Development. 
            # We don't want to fail tests just because we don't have a live API key.
            # SECURITY: Mock mode only works when Razorpay keys are placeholders
            return True

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            # 🔐 HOW: Cryptographic Check.
            # This is where Razorpay checks if the secret key matches the signature.
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            # 🚨 TAMPERING DETECTED: The signature doesn't match!
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Payment signature verification failed: {str(e)}")
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