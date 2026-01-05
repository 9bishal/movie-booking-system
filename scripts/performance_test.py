#!/usr/bin/env python
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = 'http://localhost:8000'
TEST_USERS = 10  # Simulated concurrent users
REQUESTS_PER_USER = 5

def test_endpoint(endpoint, method='GET', data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data)
        
        return {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds() * 1000,  # ms
            'success': response.status_code < 400
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'error': str(e),
            'success': False
        }

def run_performance_tests():
    """Run comprehensive performance tests"""
    endpoints = [
        ('/', 'GET'),  # Home page
        ('/movies/', 'GET'),  # Movie list
        ('/accounts/login/', 'GET'),  # Login page
        ('/accounts/register/', 'GET'),  # Register page
    ]
    
    print("🎬 Running Performance Tests")
    print("=" * 50)
    
    results = []
    
    for endpoint, method in endpoints:
        print(f"\nTesting {method} {endpoint}")
        
        # Test single request
        result = test_endpoint(endpoint, method)
        print(f"  Single request: {result['response_time']:.2f}ms")
        
        # Test concurrent requests
        with ThreadPoolExecutor(max_workers=TEST_USERS) as executor:
            futures = [executor.submit(test_endpoint, endpoint, method) 
                      for _ in range(TEST_USERS * REQUESTS_PER_USER)]
            
            concurrent_results = [f.result() for f in futures]
            
        response_times = [r['response_time'] for r in concurrent_results if r.get('response_time')]
        
        if response_times:
            stats = {
                'endpoint': endpoint,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'success_rate': sum(1 for r in concurrent_results if r.get('success', False)) / len(concurrent_results) * 100
            }
            
            print(f"  Concurrent ({TEST_USERS} users):")
            print(f"    Avg: {stats['avg_response_time']:.2f}ms")
            print(f"    Min: {stats['min_response_time']:.2f}ms")
            print(f"    Max: {stats['max_response_time']:.2f}ms")
            print(f"    Success: {stats['success_rate']:.1f}%")
            
            results.append(stats)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    for result in results:
        print(f"\n{result['endpoint']}:")
        print(f"  Average: {result['avg_response_time']:.2f}ms")
        print(f"  Range: {result['min_response_time']:.2f}ms - {result['max_response_time']:.2f}ms")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
    
    # Save results
    with open('performance_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Performance tests completed!")
    print("Results saved to performance_results.json")

if __name__ == '__main__':
    run_performance_tests()