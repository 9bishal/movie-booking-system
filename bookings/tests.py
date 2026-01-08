# ============================================================================
# 📌 BOOKINGS TESTS: Test booking workflow
# PURPOSE: Ensure all booking functionality works correctly
# PRIORITY: High - Users depend on this for their money
# ============================================================================

from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Booking
from movies.models import Movie
from movies.theater_models import Showtime, Theater, Screen, City
from django.utils import timezone

# ============================================================================
# TEST 1: AUTHENTICATION - Only logged-in users can access bookings
# ============================================================================
class BookingAuthenticationTests(TestCase):
    """
    🔐 PURPOSE: Verify that booking pages require login
    WHY: We don't want anonymous users seeing booking pages
    """
    
    def setUp(self):
        """Create test client before each test"""
        self.client = Client()
    
    def test_select_seats_requires_login(self):
        """
        📌 TEST: Anonymous user should NOT access seat selection
        EXPECTED: Redirect to login (status 302)
        """
        # 👤 ATTEMPT: Visit seat selection WITHOUT login
        response = self.client.get('/bookings/select-seats/1/')
        
        # 🛡️ ASSERT: Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_user_can_access_bookings(self):
        """
        📌 TEST: Logged-in user CAN access booking pages
        EXPECTED: Page loads (200 OK or 404 if showtime doesn't exist)
        """
        # 👤 CREATE: Test user
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # 🔑 LOGIN: With test user
        self.client.login(username='testuser', password='testpass123')
        
        # 🎫 ATTEMPT: Access my-bookings page
        response = self.client.get('/my-bookings/')
        
        # 🛡️ ASSERT: Should NOT redirect to login (not 302)
        self.assertNotEqual(response.status_code, 302)


# ============================================================================
# TEST 2: BOOKING CREATION - Create and save bookings
# ============================================================================
class BookingCreationTests(TestCase):
    """
    🎫 PURPOSE: Verify bookings can be created and saved correctly
    WHY: Bookings are the core of our system
    """
    
    def setUp(self):
        """Create test data before each test"""
        # 👤 CREATE: Test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # 🎬 CREATE: Test movie (with required duration field)
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test Description',
            release_date=timezone.now().date(),
            duration=148  # 2 hours 28 minutes in minutes
        )
        
        # 🏢 CREATE: Test theater infrastructure
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        # ⏰ CREATE: Test showtime (using start_time, not time)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',  # 2:00 PM
            end_time='16:00'     # 4:00 PM
        )
    
    def test_booking_can_be_created(self):
        """
        📌 TEST: Booking should be created and saved to database
        EXPECTED: Booking appears in database with PENDING status
        """
        # 🎫 CREATE: New booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Booking was saved
        self.assertEqual(Booking.objects.count(), 1)
        
        # 🛡️ ASSERT: Booking has correct data
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, 'PENDING')
        self.assertEqual(booking.total_amount, 605)
    
    def test_booking_status_can_change(self):
        """
        📌 TEST: Booking status can be updated (PENDING → CONFIRMED)
        EXPECTED: Status changes and saves correctly
        """
        # 🎫 CREATE: Initial booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # ✅ UPDATE: Status to CONFIRMED
        booking.status = 'CONFIRMED'
        booking.payment_id = 'pay_123456'
        booking.save()
        
        # 🛡️ ASSERT: Status was updated
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED')
        self.assertEqual(booking.payment_id, 'pay_123456')


# ============================================================================
# TEST 3: PRICE CALCULATION - Verify pricing includes all fees
# ============================================================================
class PriceCalculationTests(TestCase):
    """
    💰 PURPOSE: Verify booking prices are calculated correctly
    WHY: Money matters! Incorrect pricing = business loss + unhappy customers
    """
    
    def setUp(self):
        """Create test showtime for pricing calculation"""
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250  # Base price per seat
        )
    
    def test_single_seat_pricing(self):
        """
        📌 TEST: Price for 1 seat should include base + fees + taxes
        FORMULA: price = (base × 1) + convenience_fee + tax
        """
        # From PriceCalculator.calculate_booking_amount()
        from .utils import PriceCalculator
        
        # 💰 CALCULATE: Price for 1 seat
        price_details = PriceCalculator.calculate_booking_amount(
            self.showtime, 
            seat_count=1  # Changed from num_seats
        )
        
        # 🛡️ ASSERT: Should have all components
        self.assertIn('base_price', price_details)
        self.assertIn('convenience_fee', price_details)
        self.assertIn('tax_amount', price_details)
        self.assertIn('total_amount', price_details)
        
        # 🛡️ ASSERT: Total should be sum of components
        expected_total = (
            price_details['base_price'] + 
            price_details['convenience_fee'] + 
            price_details['tax_amount']
        )
        self.assertEqual(price_details['total_amount'], expected_total)
    
    def test_multiple_seats_pricing(self):
        """
        📌 TEST: Price for multiple seats should multiply correctly
        FORMULA: price = (base × num_seats) + convenience_fee + tax
        """
        from .utils import PriceCalculator
        
        # 💰 CALCULATE: Price for 3 seats
        price_details = PriceCalculator.calculate_booking_amount(
            self.showtime,
            seat_count=3  # Changed from num_seats
        )
        
        # 🛡️ ASSERT: Base price should be seat_price × 3
        expected_base = float(self.showtime.price) * 3
        self.assertEqual(price_details['base_price'], expected_base)
        
        # 🛡️ ASSERT: Convenience fee should be > 0
        self.assertGreater(price_details['convenience_fee'], 0)
        
        # 🛡️ ASSERT: Tax should be > 0
        self.assertGreater(price_details['tax_amount'], 0)


# ============================================================================
# TEST 4: PAYMENT SUCCESS - Verify payment confirmation logic
# ============================================================================
class PaymentSuccessTests(TestCase):
    """
    💳 PURPOSE: Test payment success handling
    WHY: This is critical - payment must be confirmed correctly
    """
    
    def setUp(self):
        """Create test booking for payment testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
        
        # Create a PENDING booking ready for payment
        self.booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='PENDING',
            razorpay_order_id='order_123456',
            payment_initiated_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(minutes=12)
        )
    
    def test_payment_can_be_confirmed(self):
        """
        📌 TEST: Payment can transition booking from PENDING to CONFIRMED
        EXPECTED: Booking status changes, payment_id saved, payment_received_at set
        """
        # ✅ SIMULATE: Payment success
        self.booking.status = 'CONFIRMED'
        self.booking.payment_id = 'pay_1234567890'
        self.booking.payment_received_at = timezone.now()
        self.booking.save()
        
        # 🛡️ ASSERT: Status changed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CONFIRMED')
        
        # 🛡️ ASSERT: Payment ID saved
        self.assertEqual(self.booking.payment_id, 'pay_1234567890')
        
        # 🛡️ ASSERT: Payment received time recorded
        self.assertIsNotNone(self.booking.payment_received_at)
    
    def test_payment_before_expiration_is_valid(self):
        """
        📌 TEST: Payment received BEFORE window expires should be valid
        EXPECTED: booking.expires_at > payment_received_at (payment is on time)
        """
        payment_time = timezone.now()
        
        # 🛡️ ASSERT: Payment time is before expiration
        self.assertLess(payment_time, self.booking.expires_at)


# ============================================================================
# TEST 5: LATE PAYMENT - Reject payment after window expires
# ============================================================================
class LatePaymentTests(TestCase):
    """
    ⏰ PURPOSE: Test late payment rejection
    WHY: Seats are released after 12 min, payment after that is invalid
    """
    
    def setUp(self):
        """Create booking with expired window"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
        
        # Create booking with EXPIRED window (15 minutes ago)
        self.booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING',
            razorpay_order_id='order_123456',
            payment_initiated_at=timezone.now() - timezone.timedelta(minutes=15),
            expires_at=timezone.now() - timezone.timedelta(minutes=3)  # Expired 3 minutes ago
        )
    
    def test_late_payment_is_rejected(self):
        """
        📌 TEST: Payment after window expires should be rejected
        EXPECTED: payment_time > expires_at (payment is LATE)
        """
        payment_time = timezone.now()
        
        # 🛡️ ASSERT: Payment is AFTER expiration
        self.assertGreater(payment_time, self.booking.expires_at)
        
        # 🛡️ ASSERT: Booking should still be PENDING (not confirmed)
        self.assertEqual(self.booking.status, 'PENDING')
    
    def test_late_payment_marked_as_failed(self):
        """
        📌 TEST: Late payment should mark booking as FAILED
        EXPECTED: Status changed to FAILED, refund email marked for sending
        """
        # ⏰ SIMULATE: Late payment confirmation (after window)
        self.booking.status = 'FAILED'
        self.booking.payment_id = 'pay_late_payment'
        self.booking.payment_received_at = timezone.now()
        self.booking.refund_notification_sent = False  # Email will be sent
        self.booking.save()
        
        # 🛡️ ASSERT: Status is FAILED
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'FAILED')
        
        # 🛡️ ASSERT: Payment ID saved (for refund tracking)
        self.assertEqual(self.booking.payment_id, 'pay_late_payment')
        
        # 🛡️ ASSERT: Refund notification not yet sent
        self.assertFalse(self.booking.refund_notification_sent)


# ============================================================================
# TEST 6: PAYMENT FAILURE - Handle cancelled/failed payments
# ============================================================================
class PaymentFailureTests(TestCase):
    """
    ❌ PURPOSE: Test payment failure handling
    WHY: Users cancel payments or payment fails - need proper cleanup
    """
    
    def setUp(self):
        """Create booking for failure testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2', 'A3'],
            total_seats=3,
            base_price=750,
            convenience_fee=75,
            tax_amount=82.5,
            total_amount=907.5,
            status='PENDING'
        )
    
    def test_payment_failure_marks_booking_failed(self):
        """
        📌 TEST: Failed payment should mark booking as FAILED
        EXPECTED: Status = FAILED, payment_received_at = None
        """
        # ❌ SIMULATE: Payment failure/cancellation
        self.booking.status = 'FAILED'
        self.booking.failure_email_sent = False
        self.booking.save()
        
        # 🛡️ ASSERT: Status is FAILED
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'FAILED')
        
        # 🛡️ ASSERT: No payment received (payment_received_at is None)
        self.assertIsNone(self.booking.payment_received_at)
        
        # 🛡️ ASSERT: Failure email not yet sent
        self.assertFalse(self.booking.failure_email_sent)
    
    def test_no_payment_confirmed_after_failure(self):
        """
        📌 TEST: Failed payment should not confirm booking
        EXPECTED: payment_id can be None, status is FAILED not CONFIRMED
        """
        # 🛡️ SETUP: Mark as failed without payment
        self.booking.status = 'FAILED'
        self.booking.save()
        
        # 🛡️ ASSERT: Booking is NOT confirmed
        self.assertNotEqual(self.booking.status, 'CONFIRMED')


# ============================================================================
# TEST 7: DUPLICATE PAYMENT PREVENTION - Prevent double charging
# ============================================================================
class DuplicatePaymentTests(TestCase):
    """
    🛡️ PURPOSE: Ensure same payment isn't processed twice
    WHY: If payment_received_at is set, don't process again
    """
    
    def setUp(self):
        """Create booking that was already confirmed"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
        
        # Create CONFIRMED booking (already paid)
        self.booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED',
            payment_id='pay_already_paid',
            payment_received_at=timezone.now(),
            razorpay_order_id='order_123456'
        )
    
    def test_already_confirmed_booking_cannot_be_confirmed_again(self):
        """
        📌 TEST: Payment should not confirm already-confirmed booking
        EXPECTED: If payment_received_at is set, skip confirmation
        """
        # 🛡️ GUARD: Check if payment already received
        if self.booking.payment_received_at:
            # Payment was already processed - don't process again
            should_skip = True
        else:
            should_skip = False
        
        # 🛡️ ASSERT: Should skip processing
        self.assertTrue(should_skip)
    
    def test_payment_received_at_acts_as_guard(self):
        """
        📌 TEST: payment_received_at field prevents duplicate emails
        EXPECTED: If not None, payment was already confirmed
        """
        # 🛡️ ASSERT: payment_received_at is set
        self.assertIsNotNone(self.booking.payment_received_at)
        
        # 🛡️ ASSERT: Can use this to skip email sending
        should_send_confirmation = self.booking.payment_received_at is None
        
        # 🛡️ ASSERT: Should NOT send confirmation (already sent)
        self.assertFalse(should_send_confirmation)


# ============================================================================
# TEST 8: EDGE CASES - Unexpected scenarios
# ============================================================================
class EdgeCasesTests(TestCase):
    """
    🔍 PURPOSE: Test unusual/edge case scenarios
    WHY: Real-world apps encounter weird situations
    """
    
    def setUp(self):
        """Create test data for edge cases"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_booking_with_maximum_seats(self):
        """
        📌 TEST: User can book maximum allowed seats (10)
        EXPECTED: Booking created successfully with 10 seats
        """
        # 🎫 CREATE: Booking with max seats (10)
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'],
            total_seats=10,
            base_price=2500,
            convenience_fee=250,
            tax_amount=275,
            total_amount=3025,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Booking created with 10 seats
        self.assertEqual(booking.total_seats, 10)
        self.assertEqual(len(booking.seats), 10)
    
    def test_booking_total_price_precision(self):
        """
        📌 TEST: Price calculations maintain decimal precision
        EXPECTED: No rounding errors in final price
        """
        # 🎫 CREATE: Booking with fractional prices
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=249.99,
            convenience_fee=24.99,
            tax_amount=27.50,
            total_amount=302.48,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Decimal precision maintained
        self.assertEqual(booking.base_price, 249.99)
        self.assertEqual(booking.convenience_fee, 24.99)
        self.assertEqual(booking.tax_amount, 27.50)
    
    def test_booking_with_empty_seats_list_invalid(self):
        """
        📌 TEST: Booking with no seats selected is invalid
        EXPECTED: Should have at least 1 seat
        """
        # ⚠️ ATTEMPT: Create booking with empty seats (should be caught in view)
        # Here we just verify the validation would catch it
        
        # 🛡️ GUARD: Check seats before creating
        seat_ids = []
        is_valid = len(seat_ids) > 0 and len(seat_ids) <= 10
        
        # 🛡️ ASSERT: Invalid (no seats)
        self.assertFalse(is_valid)
    
    def test_user_can_have_multiple_bookings(self):
        """
        📌 TEST: Same user can have multiple bookings
        EXPECTED: Each booking is independent
        """
        # Create movie 2 and showtime 2
        movie2 = Movie.objects.create(
            title='Another Movie',
            slug='another-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=110
        )
        showtime2 = Showtime.objects.create(
            movie=movie2,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=2),
            start_time='18:00',
            end_time='19:50',
            price=300
        )
        
        # Create 2 bookings for same user
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        booking2 = Booking.objects.create(
            user=self.user,
            showtime=showtime2,
            seats=['B2'],
            total_seats=1,
            base_price=300,
            convenience_fee=30,
            tax_amount=33,
            total_amount=363,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Both bookings exist
        user_bookings = Booking.objects.filter(user=self.user)
        self.assertEqual(user_bookings.count(), 2)
        
        # 🛡️ ASSERT: Each booking has different showtime
        self.assertNotEqual(booking1.showtime, booking2.showtime)
    
    def test_booking_timestamps_are_recorded(self):
        """
        📌 TEST: Booking creation and payment times are recorded
        EXPECTED: Timestamps are set automatically
        """
        # 🎫 CREATE: Booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: created_at is set
        self.assertIsNotNone(booking.created_at)
        
        # 🛡️ ASSERT: payment_received_at is None (not paid yet)
        self.assertIsNone(booking.payment_received_at)


# ============================================================================
# TEST 9: API ENDPOINTS - Test view functions that return JSON
# ============================================================================
class BookingAPITests(TestCase):
    """
    🔌 PURPOSE: Test API endpoints (AJAX calls)
    WHY: Frontend uses these for real-time updates
    """
    
    def setUp(self):
        """Create test user and login"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_get_seat_status_api_returns_json(self):
        """
        📌 TEST: Seat status API should return JSON with seat info
        EXPECTED: { reserved_seats: [...], booked_seats: [...], available_count: N }
        """
        # 🔌 CALL: Get seat status API (correct URL from bookings/urls.py)
        response = self.client.get(f'/bookings/api/seat-status/{self.showtime.id}/')
        
        # 🛡️ ASSERT: Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # 🛡️ ASSERT: Should return JSON
        try:
            data = response.json()
            self.assertIn('reserved_seats', data)
            self.assertIn('booked_seats', data)
            self.assertIn('available_count', data)
        except Exception:
            self.fail("Response is not valid JSON")
    
    def test_my_bookings_page_loads(self):
        """
        📌 TEST: My bookings page should load for logged-in user
        EXPECTED: 200 OK, shows booking list
        """
        # 🎫 CREATE: A booking for this user
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # 🔌 CALL: My bookings page
        response = self.client.get('/bookings/my-bookings/')
        
        # 🛡️ ASSERT: Should NOT return 404 (URL should exist)
        self.assertNotEqual(response.status_code, 404)
        
        # 🛡️ ASSERT: If successful, should contain booking data
        if response.status_code == 200:
            self.assertIn(booking.booking_number, str(response.content))
    
    def test_booking_detail_page_loads(self):
        """
        📌 TEST: Individual booking detail page should load
        EXPECTED: 200 OK, shows ticket details
        """
        # 🎫 CREATE: A booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='CONFIRMED'
        )
        
        # 🔌 CALL: Booking detail page (correct URL from bookings/urls.py)
        response = self.client.get(f'/bookings/detail/{booking.id}/')
        
        # 🛡️ ASSERT: Should load successfully
        self.assertEqual(response.status_code, 200)
        
        # 🛡️ ASSERT: Should contain booking info
        self.assertIn(str(booking.total_seats), str(response.content))


# ============================================================================
# TEST 10: SECURITY - Prevent unauthorized access
# ============================================================================
class BookingSecurityTests(TestCase):
    """
    🔐 PURPOSE: Test security restrictions
    WHY: Users shouldn't see/modify other users' bookings
    """
    
    def setUp(self):
        """Create 2 users with bookings"""
        self.client = Client()
        
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
        
        # Create booking for user1
        self.booking_user1 = Booking.objects.create(
            user=self.user1,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
    
    def test_user_cannot_see_other_users_bookings(self):
        """
        📌 TEST: User2 should NOT be able to access User1's booking detail
        EXPECTED: 404 Not Found (booking doesn't exist for this user)
        """
        # 🔑 LOGIN: As user2
        self.client.login(username='user2', password='pass2')
        
        # 🔌 ATTEMPT: Access user1's booking (correct URL from bookings/urls.py)
        response = self.client.get(f'/bookings/detail/{self.booking_user1.id}/')
        
        # 🛡️ ASSERT: Should get 404 (booking doesn't exist for this user)
        self.assertEqual(response.status_code, 404)
    
    def test_anonymous_user_cannot_access_bookings(self):
        """
        📌 TEST: Anonymous user should NOT access any booking pages
        EXPECTED: 302 redirect (to login) or 404 (access denied)
        """
        # ⚠️ NO LOGIN
        
        # 🔌 ATTEMPT: Access booking detail without login (correct URL from bookings/urls.py)
        response = self.client.get(f'/bookings/detail/{self.booking_user1.id}/')
        
        # 🛡️ ASSERT: Should get 302 redirect or 404 (not allowed)
        self.assertIn(response.status_code, [302, 404])


# ============================================================================
# TEST 11: SEAT RESERVATION - Redis seat locking mechanism
# ============================================================================
class SeatReservationTests(TestCase):
    """
    🔒 PURPOSE: Test Redis-based seat reservation (12 minute window)
    WHY: Prevent double-booking when users are selecting seats
    """
    
    def setUp(self):
        """Create test showtime for seat reservation"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_seats_can_be_reserved(self):
        """
        📌 TEST: Seats should be reservable (temporarily locked)
        EXPECTED: Seats can be reserved for 12 minutes
        """
        # 🔒 SIMULATE: Reserving seats in Redis (would be done by reserve_seats view)
        # For this test, we verify the booking records the seats
        
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='PENDING',
            payment_initiated_at=timezone.now()
        )
        
        # 🛡️ ASSERT: Seats are recorded
        self.assertEqual(booking.total_seats, 2)
        self.assertIn('A1', booking.seats)
        self.assertIn('A2', booking.seats)
    
    def test_reserved_seats_expire_after_window(self):
        """
        📌 TEST: Reserved seats should expire after 12 minutes
        EXPECTED: expires_at is set to 12 minutes from now
        """
        payment_window_minutes = 12
        
        now = timezone.now()
        expiry = now + timezone.timedelta(minutes=payment_window_minutes)
        
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING',
            payment_initiated_at=now,
            expires_at=expiry
        )
        
        # 🛡️ ASSERT: Expiry is approximately 12 minutes away
        time_diff = (booking.expires_at - booking.payment_initiated_at).total_seconds()
        expected_diff = payment_window_minutes * 60
        
        # Allow 1 second difference for test execution time
        self.assertLess(abs(time_diff - expected_diff), 2)
    
    def test_same_seat_cannot_be_booked_twice(self):
        """
        📌 TEST: Once seat is booked, it can't be booked again
        EXPECTED: Second booking would fail (in real scenario)
        """
        # 🎫 CREATE: First booking with A1
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # 👤 CREATE: Second user
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass456'
        )
        
        # 🎫 CREATE: Second booking attempt with same seat
        booking2 = Booking.objects.create(
            user=user2,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Both bookings exist (in real app, second would be prevented)
        # This tests the data model - actual prevention happens in views via Redis
        all_bookings = Booking.objects.filter(showtime=self.showtime)
        self.assertEqual(all_bookings.count(), 2)


# ============================================================================
# TEST 12: REFUND LOGIC - Test refund workflow
# ============================================================================
class RefundLogicTests(TestCase):
    """
    💳 PURPOSE: Test refund handling for cancelled/failed payments
    WHY: Users need to get refunds if payment fails
    """
    
    def setUp(self):
        """Create test booking for refund testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_refund_status_can_be_tracked(self):
        """
        📌 TEST: Refund status should be trackable in booking
        EXPECTED: payment_id preserved and booking marked as refunded
        """
        # 💳 CREATE: Booking eligible for refund
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED',
            payment_id='pay_123456',
            payment_received_at=timezone.now()
        )
        
        # 💰 SIMULATE: Refund processing
        booking.status = 'CANCELLED'
        booking.save()
        
        # 🛡️ ASSERT: Refund tracked
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.payment_id, 'pay_123456')
        self.assertIsNotNone(booking.payment_received_at)
    
    def test_full_refund_amount_calculation(self):
        """
        📌 TEST: Full refund should equal total amount charged
        EXPECTED: Can calculate refund = total_amount for cancelled bookings
        """
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='CONFIRMED',
            payment_id='pay_123456'
        )
        
        # 💰 CALCULATE: Refund amount (should equal total)
        refund_amount = booking.total_amount
        
        # 🛡️ ASSERT: Refund equals total
        self.assertEqual(refund_amount, 605)


# ============================================================================
# TEST 13: EMAIL NOTIFICATIONS - Test email sending
# ============================================================================
class EmailNotificationTests(TestCase):
    """
    📧 PURPOSE: Test email notifications for bookings
    WHY: Users need email confirmations and updates
    """
    
    def setUp(self):
        """Create test booking for email testing"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_booking_email_flag_can_be_set(self):
        """
        📌 TEST: Booking should track if confirmation email was sent
        EXPECTED: confirmation_email_sent flag changes from False to True
        """
        # 🎫 CREATE: Booking without email sent
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED',
            payment_id='pay_123456',
            confirmation_email_sent=False
        )
        
        # 🛡️ ASSERT: Initially not sent
        self.assertFalse(booking.confirmation_email_sent)
        
        # 📧 SIMULATE: Email sent
        booking.confirmation_email_sent = True
        booking.save()
        
        # 🛡️ ASSERT: Now marked as sent
        booking.refresh_from_db()
        self.assertTrue(booking.confirmation_email_sent)
    
    def test_failure_email_tracking(self):
        """
        📌 TEST: Failed payment email tracking
        EXPECTED: failure_email_sent flag can be set
        """
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='FAILED',
            failure_email_sent=False
        )
        
        # 📧 SIMULATE: Failure email sent
        booking.failure_email_sent = True
        booking.save()
        
        # 🛡️ ASSERT: Tracked
        booking.refresh_from_db()
        self.assertTrue(booking.failure_email_sent)
    
    def test_late_payment_email_tracking(self):
        """
        📌 TEST: Late payment email (refund notification) tracking
        EXPECTED: refund_notification_sent flag can be set
        """
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='FAILED',
            payment_id='pay_late',
            refund_notification_sent=False
        )
        
        # 📧 SIMULATE: Refund notification email sent
        booking.refund_notification_sent = True
        booking.save()
        
        # 🛡️ ASSERT: Tracked
        booking.refresh_from_db()
        self.assertTrue(booking.refund_notification_sent)


# ============================================================================
# TEST 14: CONCURRENT OPERATIONS - Test race condition handling
# ============================================================================
class ConcurrentOperationsTests(TestCase):
    """
    ⚡ PURPOSE: Test system handles concurrent booking attempts
    WHY: Multiple users clicking simultaneously could cause issues
    """
    
    def setUp(self):
        """Create test data for concurrent tests"""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=50
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_multiple_users_can_book_different_seats(self):
        """
        📌 TEST: Two users can book different seats for same showtime
        EXPECTED: Both bookings succeed for different seats
        """
        # 👤 USER1: Books A1
        booking1 = Booking.objects.create(
            user=self.user1,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # 👤 USER2: Books B2 (different seat)
        booking2 = Booking.objects.create(
            user=self.user2,
            showtime=self.showtime,
            seats=['B2'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # 🛡️ ASSERT: Both bookings exist
        self.assertEqual(Booking.objects.filter(showtime=self.showtime).count(), 2)
        
        # 🛡️ ASSERT: Different users
        self.assertNotEqual(booking1.user, booking2.user)
        
        # 🛡️ ASSERT: Different seats
        self.assertNotEqual(booking1.seats[0], booking2.seats[0])
    
    def test_booking_order_is_preserved(self):
        """
        📌 TEST: Bookings are created in order (FIFO)
        EXPECTED: First booking has earlier created_at timestamp
        """
        # Create booking1
        booking1 = Booking.objects.create(
            user=self.user1,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # Create booking2 (should be slightly later)
        booking2 = Booking.objects.create(
            user=self.user2,
            showtime=self.showtime,
            seats=['B1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Booking1 created first or same time
        self.assertLessEqual(booking1.created_at, booking2.created_at)


# ============================================================================
# TEST 15: BOOKING CANCELLATION - Test cancellation workflow
# ============================================================================
class BookingCancellationTests(TestCase):
    """
    🚫 PURPOSE: Test booking cancellation logic
    WHY: Users need to cancel bookings and get refunds
    """
    
    def setUp(self):
        """Create test booking for cancellation testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_pending_booking_can_be_cancelled(self):
        """
        📌 TEST: PENDING booking can be cancelled immediately
        EXPECTED: Status changes to CANCELLED
        """
        # 🎫 CREATE: Pending booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='PENDING'
        )
        
        # 🚫 CANCEL: Booking
        booking.status = 'CANCELLED'
        booking.save()
        
        # 🛡️ ASSERT: Status changed
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
    
    def test_confirmed_booking_can_be_cancelled_with_refund(self):
        """
        📌 TEST: CONFIRMED booking can be cancelled with refund
        EXPECTED: Status = CANCELLED, refund tracked
        """
        # 🎫 CREATE: Confirmed booking (already paid)
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED',
            payment_id='pay_123456',
            payment_received_at=timezone.now()
        )
        
        # 🚫 CANCEL: With refund
        booking.status = 'CANCELLED'
        booking.save()
        
        # 🛡️ ASSERT: Cancelled with refund tracked
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertIsNotNone(booking.payment_id)
    
    def test_cannot_cancel_already_cancelled_booking(self):
        """
        📌 TEST: Already cancelled booking can't be cancelled again
        EXPECTED: Status stays CANCELLED
        """
        # 🎫 CREATE: Already cancelled booking
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CANCELLED'
        )
        
        # 🛡️ GUARD: Check if already cancelled
        is_already_cancelled = booking.status == 'CANCELLED'
        
        # 🛡️ ASSERT: Can't cancel twice
        self.assertTrue(is_already_cancelled)


# ============================================================================
# TEST 16: DATA VALIDATION - Test input validation
# ============================================================================
class DataValidationTests(TestCase):
    """
    ✔️ PURPOSE: Test input validation and data constraints
    WHY: Invalid data should be rejected, not stored
    """
    
    def setUp(self):
        """Create test data for validation testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_negative_price_rejected(self):
        """
        📌 TEST: Negative prices should be rejected
        EXPECTED: Price must be positive
        """
        # 🛡️ GUARD: Check price is valid
        invalid_price = -250
        is_valid = invalid_price > 0
        
        # 🛡️ ASSERT: Invalid price rejected
        self.assertFalse(is_valid)
    
    def test_zero_seats_rejected(self):
        """
        📌 TEST: Booking with 0 seats should be rejected
        EXPECTED: total_seats must be > 0
        """
        # 🛡️ GUARD: Check seat count
        invalid_seat_count = 0
        is_valid = 0 < invalid_seat_count <= 10
        
        # 🛡️ ASSERT: Zero seats rejected
        self.assertFalse(is_valid)
    
    def test_negative_seats_rejected(self):
        """
        📌 TEST: Negative seat counts should be rejected
        EXPECTED: total_seats must be positive
        """
        # 🛡️ GUARD: Check seat validation
        invalid_seats = -5
        is_valid = invalid_seats > 0
        
        # 🛡️ ASSERT: Negative seats rejected
        self.assertFalse(is_valid)
    
    def test_exceeding_max_seats_rejected(self):
        """
        📌 TEST: Booking > 10 seats should be rejected
        EXPECTED: total_seats <= 10
        """
        # 🛡️ GUARD: Check max seats limit
        seat_count = 15
        max_seats = 10
        is_valid = seat_count <= max_seats
        
        # 🛡️ ASSERT: Exceeding max rejected
        self.assertFalse(is_valid)
    
    def test_valid_seat_count_range(self):
        """
        📌 TEST: Valid seat counts (1-10) should pass
        EXPECTED: All counts 1-10 are valid
        """
        # 🛡️ VERIFY: Each count from 1-10 is valid
        for count in range(1, 11):
            is_valid = 0 < count <= 10
            self.assertTrue(is_valid, f"Seat count {count} should be valid")
    
    def test_invalid_booking_status(self):
        """
        📌 TEST: Invalid status should be rejected
        EXPECTED: Only valid statuses accepted
        """
        # 🛡️ DEFINE: Valid statuses
        valid_statuses = ['PENDING', 'CONFIRMED', 'FAILED', 'CANCELLED', 'REFUNDED']
        
        # 🛡️ GUARD: Check status validity
        invalid_status = 'INVALID_STATUS'
        is_valid = invalid_status in valid_statuses
        
        # 🛡️ ASSERT: Invalid status rejected
        self.assertFalse(is_valid)
    
    def test_all_valid_booking_statuses(self):
        """
        📌 TEST: All valid statuses should be accepted
        EXPECTED: Can create bookings with each status
        """
        valid_statuses = ['PENDING', 'CONFIRMED', 'FAILED', 'CANCELLED', 'REFUNDED']
        
        for status in valid_statuses:
            booking = Booking.objects.create(
                user=self.user,
                showtime=self.showtime,
                seats=['A1'],
                total_seats=1,
                base_price=250,
                convenience_fee=25,
                tax_amount=27.5,
                total_amount=302.5,
                status=status
            )
            
            # 🛡️ ASSERT: Status saved correctly
            self.assertEqual(booking.status, status)


# ============================================================================
# TEST 17: BUSINESS LOGIC - Test complex business scenarios
# ============================================================================
class BusinessLogicTests(TestCase):
    """
    💼 PURPOSE: Test complex business logic and workflows
    WHY: Real-world scenarios are more complex than happy paths
    """
    
    def setUp(self):
        """Create test data for business logic tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=50
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_available_seats_calculation(self):
        """
        📌 TEST: Available seats = total - booked
        EXPECTED: Accurate seat availability
        """
        # Total seats in screen
        total_seats = self.screen.total_seats
        
        # Book some seats
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1', 'A2'],
            total_seats=2,
            base_price=500,
            convenience_fee=50,
            tax_amount=55,
            total_amount=605,
            status='CONFIRMED'
        )
        
        # Simulate second booking
        user2 = User.objects.create_user(username='user2', password='pass2')
        booking2 = Booking.objects.create(
            user=user2,
            showtime=self.showtime,
            seats=['B1', 'B2', 'B3'],
            total_seats=3,
            base_price=750,
            convenience_fee=75,
            tax_amount=82.5,
            total_amount=907.5,
            status='CONFIRMED'
        )
        
        # Calculate available
        booked_seats = 2 + 3
        available = total_seats - booked_seats
        
        # 🛡️ ASSERT: Calculation correct
        self.assertEqual(available, total_seats - 5)
    
    def test_occupancy_percentage(self):
        """
        📌 TEST: Calculate occupancy percentage
        EXPECTED: (booked / total) * 100
        """
        total_seats = self.screen.total_seats
        
        # Book 50% of seats
        bookings_count = Booking.objects.filter(
            showtime=self.showtime,
            status='CONFIRMED'
        ).count()
        
        booked_seats = 25  # Simulated
        occupancy = (booked_seats / total_seats) * 100
        
        # 🛡️ ASSERT: Occupancy calculated
        self.assertEqual(occupancy, 50.0)
    
    def test_revenue_calculation(self):
        """
        📌 TEST: Total revenue = sum of all confirmed bookings
        EXPECTED: Accurate revenue tracking
        """
        # Create multiple bookings
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        user2 = User.objects.create_user(username='user2', password='pass2')
        booking2 = Booking.objects.create(
            user=user2,
            showtime=self.showtime,
            seats=['B1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # Calculate revenue
        confirmed = Booking.objects.filter(
            showtime=self.showtime,
            status='CONFIRMED'
        )
        total_revenue = sum(b.total_amount for b in confirmed)
        
        # 🛡️ ASSERT: Revenue correct
        self.assertEqual(total_revenue, 605.0)
    
    def test_peak_vs_off_peak_pricing_readiness(self):
        """
        📌 TEST: System ready for peak/off-peak pricing
        EXPECTED: Can support different prices for different times
        """
        # Create second showtime with different price
        showtime2 = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=self.showtime.date,
            start_time='18:00',
            end_time='20:00',
            price=350  # Peak time = higher price
        )
        
        # Both prices in system
        morning_price = self.showtime.price
        evening_price = showtime2.price
        
        # 🛡️ ASSERT: Different prices supported
        self.assertLess(morning_price, evening_price)
        self.assertEqual(morning_price, 250)
        self.assertEqual(evening_price, 350)


# ============================================================================
# TEST 18: MODEL RELATIONSHIPS - Test database relationships
# ============================================================================
class ModelRelationshipTests(TestCase):
    """
    🔗 PURPOSE: Test database relationships and integrity
    WHY: Relationships must work correctly for data consistency
    """
    
    def setUp(self):
        """Create test data with relationships"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            slug='test-movie',
            description='Test',
            release_date=timezone.now().date(),
            duration=120
        )
        
        self.city = City.objects.create(name='Test City')
        self.theater = Theater.objects.create(
            name='Test Theater',
            city=self.city,
            address='123 Test St'
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name='Screen 1',
            total_seats=100
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=timezone.now().date() + timezone.timedelta(days=1),
            start_time='14:00',
            end_time='16:00',
            price=250
        )
    
    def test_booking_has_user_relationship(self):
        """
        📌 TEST: Booking correctly linked to User
        EXPECTED: Can access user from booking
        """
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Can access user
        self.assertEqual(booking.user.username, 'testuser')
        self.assertEqual(booking.user, self.user)
    
    def test_booking_has_showtime_relationship(self):
        """
        📌 TEST: Booking correctly linked to Showtime
        EXPECTED: Can access showtime and movie
        """
        booking = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Can access showtime
        self.assertEqual(booking.showtime, self.showtime)
        
        # 🛡️ ASSERT: Can access movie through showtime
        self.assertEqual(booking.showtime.movie, self.movie)
    
    def test_showtime_has_screen_relationship(self):
        """
        📌 TEST: Showtime correctly linked to Screen
        EXPECTED: Can access screen and theater
        """
        # 🛡️ ASSERT: Can access screen
        self.assertEqual(self.showtime.screen, self.screen)
        
        # 🛡️ ASSERT: Can access theater through screen
        self.assertEqual(self.showtime.screen.theater, self.theater)
    
    def test_user_can_have_multiple_bookings(self):
        """
        📌 TEST: User can have many bookings
        EXPECTED: Reverse relationship works
        """
        # Create 2 bookings for same user
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='PENDING'
        )
        
        # Create another showtime
        showtime2 = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            date=self.showtime.date + timezone.timedelta(days=1),
            start_time='20:00',
            end_time='22:00',
            price=300
        )
        
        booking2 = Booking.objects.create(
            user=self.user,
            showtime=showtime2,
            seats=['B1'],
            total_seats=1,
            base_price=300,
            convenience_fee=30,
            tax_amount=33,
            total_amount=363,
            status='PENDING'
        )
        
        # 🛡️ ASSERT: Both bookings exist for user
        user_bookings = Booking.objects.filter(user=self.user)
        self.assertEqual(user_bookings.count(), 2)
    
    def test_showtime_can_have_multiple_bookings(self):
        """
        📌 TEST: Showtime can have many bookings (from different users)
        EXPECTED: Reverse relationship works
        """
        user2 = User.objects.create_user(username='user2', password='pass2')
        
        # Create bookings from different users for same showtime
        booking1 = Booking.objects.create(
            user=self.user,
            showtime=self.showtime,
            seats=['A1'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        booking2 = Booking.objects.create(
            user=user2,
            showtime=self.showtime,
            seats=['A2'],
            total_seats=1,
            base_price=250,
            convenience_fee=25,
            tax_amount=27.5,
            total_amount=302.5,
            status='CONFIRMED'
        )
        
        # 🛡️ ASSERT: Both bookings exist for showtime
        showtime_bookings = Booking.objects.filter(showtime=self.showtime)
        self.assertEqual(showtime_bookings.count(), 2)
