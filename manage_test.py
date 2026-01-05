#!/usr/bin/env python
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moviebooking.settings")
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(
        verbosity=2,
        failfast=False,
        keepdb=True  # Keep test database between runs
    )
    
    # Run all tests
    failures = test_runner.run_tests([
        'accounts.tests',
        'movies.tests',
        'bookings.tests',
        'dashboard.tests',
    ])
    
    sys.exit(bool(failures))