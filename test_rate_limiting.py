#!/usr/bin/env python
"""
Rate Limiting Test Script

This script tests the rate limiting functionality by making
multiple requests to the seat reservation endpoint.

Usage:
    python test_rate_limiting.py
"""

import time
import sys


def test_rate_limit_configuration():
    """Test that rate limiters are configured correctly"""
    print("=" * 70)
    print("🧪 RATE LIMITING CONFIGURATION TEST")
    print("=" * 70)
    
    try:
        from utils.rate_limit import (
            login_limiter,
            seat_selection_limiter,
            booking_limiter,
            payment_limiter,
            api_limiter
        )
        
        limiters = {
            'Login Limiter': login_limiter,
            'Seat Selection Limiter': seat_selection_limiter,
            'Booking Limiter': booking_limiter,
            'Payment Limiter': payment_limiter,
            'API Limiter': api_limiter,
        }
        
        print("\n✅ All rate limiters imported successfully!\n")
        
        for name, limiter in limiters.items():
            num, period = limiter.parse_rate(limiter.rate)
            print(f"📊 {name}:")
            print(f"   Rate: {limiter.rate}")
            print(f"   Allows: {num} requests per {period} seconds")
            print(f"   Key Prefix: {limiter.key_prefix}")
            print()
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERROR: Failed to import rate limiters")
        print(f"   {str(e)}")
        return False


def test_parse_rate():
    """Test rate parsing functionality"""
    print("=" * 70)
    print("🧪 RATE PARSING TEST")
    print("=" * 70)
    
    try:
        from utils.rate_limit import RateLimiter
        
        test_cases = [
            ('5/s', 5, 1, '5 per second'),
            ('10/m', 10, 60, '10 per minute'),
            ('100/h', 100, 3600, '100 per hour'),
            ('1000/d', 1000, 86400, '1000 per day'),
        ]
        
        print()
        all_passed = True
        
        for rate_str, expected_num, expected_period, description in test_cases:
            limiter = RateLimiter(rate=rate_str)
            num, period = limiter.parse_rate(rate_str)
            
            if num == expected_num and period == expected_period:
                print(f"✅ {description}: PASSED")
                print(f"   Input: {rate_str} → Output: {num} requests / {period}s")
            else:
                print(f"❌ {description}: FAILED")
                print(f"   Expected: {expected_num} / {expected_period}s")
                print(f"   Got: {num} / {period}s")
                all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_redis_connection():
    """Test Redis connection for rate limiting"""
    print("=" * 70)
    print("🧪 REDIS CONNECTION TEST")
    print("=" * 70)
    
    try:
        from django.core.cache import cache
        
        print("\n⏳ Testing Redis connection...")
        
        # Test write
        test_key = 'rate_limit_test_key'
        test_value = 'test_value_123'
        cache.set(test_key, test_value, 10)
        
        # Test read
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis connection successful!")
            print(f"   Write: {test_key} = {test_value}")
            print(f"   Read: {test_key} = {retrieved_value}")
            
            # Cleanup
            cache.delete(test_key)
            print("   Cleanup: Test key deleted")
            print()
            return True
        else:
            print("❌ Redis connection failed!")
            print(f"   Expected: {test_value}")
            print(f"   Got: {retrieved_value}")
            print()
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Redis connection failed")
        print(f"   {str(e)}")
        print("\n💡 Make sure Redis is running:")
        print("   $ redis-cli ping")
        print()
        return False


def test_rate_limiter_logic():
    """Test the rate limiting logic"""
    print("=" * 70)
    print("🧪 RATE LIMITER LOGIC TEST")
    print("=" * 70)
    
    try:
        from django.core.cache import cache
        from django.test import RequestFactory
        from django.contrib.auth.models import User, AnonymousUser
        from utils.rate_limit import RateLimiter
        
        # Create a test limiter (3 requests per minute)
        test_limiter = RateLimiter(rate='3/m', key_prefix='test')
        factory = RequestFactory()
        
        print("\n⏳ Testing rate limiter with 3 requests/minute limit...\n")
        
        # Create mock request
        request = factory.get('/')
        request.user = AnonymousUser()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Clear any existing rate limit data
        cache.clear()
        
        results = []
        for i in range(5):
            allowed, num, period = test_limiter.is_allowed(request)
            results.append(allowed)
            status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
            print(f"Request {i+1}: {status}")
        
        # Expected: First 3 allowed, last 2 blocked
        expected = [True, True, True, False, False]
        
        if results == expected:
            print("\n✅ Rate limiter logic test PASSED!")
            print(f"   Expected: {expected}")
            print(f"   Got: {results}")
            print()
            return True
        else:
            print("\n❌ Rate limiter logic test FAILED!")
            print(f"   Expected: {expected}")
            print(f"   Got: {results}")
            print()
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary"""
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print()
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print()
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Rate limiting is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
    
    print("=" * 70)
    
    return failed == 0


def main():
    """Run all tests"""
    print("\n")
    print("🚀 Starting Rate Limiting Tests...")
    print()
    
    # Setup Django
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
    django.setup()
    
    # Run tests
    results = {
        'Configuration Test': test_rate_limit_configuration(),
        'Rate Parsing Test': test_parse_rate(),
        'Redis Connection Test': test_redis_connection(),
        'Rate Limiter Logic Test': test_rate_limiter_logic(),
    }
    
    # Print summary
    success = print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
