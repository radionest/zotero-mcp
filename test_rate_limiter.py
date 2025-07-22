#!/usr/bin/env python3
"""
Test script for verifying rate limiter functionality.
"""

import logging
import time
from datetime import datetime

import sys
sys.path.insert(0, 'src')

from zotero_mcp.client import get_zotero_client
from zotero_mcp.rate_limiter import RateLimitedZoteroClient

# Configure logging to see rate limiter messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_rate_limiter():
    """Test the rate limiter with actual Zotero API calls."""
    print("Testing Zotero API rate limiter...")
    print("-" * 50)
    
    try:
        # Get standard Zotero client
        standard_client = get_zotero_client()
        
        # Wrap with rate limiter
        rate_limited_client = RateLimitedZoteroClient(standard_client)
        
        # Test 1: Make several rapid requests to trigger rate limiting
        print("\nTest 1: Rapid sequential requests")
        print("Making 5 rapid API calls...")
        
        start_time = time.time()
        for i in range(5):
            try:
                print(f"\nRequest {i + 1}:")
                request_start = time.time()
                
                # Make a simple API call
                items = rate_limited_client.items(limit=1)
                
                request_end = time.time()
                print(f"  - Completed in {request_end - request_start:.2f}s")
                print(f"  - Retrieved {len(items)} item(s)")
                
            except Exception as e:
                print(f"  - Error: {e}")
        
        total_time = time.time() - start_time
        print(f"\nTotal time for 5 requests: {total_time:.2f}s")
        print(f"Average time per request: {total_time / 5:.2f}s")
        
        # Test 2: Fetch items in batches (simulating database update)
        print("\n" + "-" * 50)
        print("\nTest 2: Batch fetching simulation")
        print("Fetching items in batches of 50...")
        
        total_items = 0
        batch_count = 0
        start_time = time.time()
        
        for start in range(0, 150, 50):  # Fetch up to 150 items
            try:
                batch_start = time.time()
                items = rate_limited_client.items(start=start, limit=50)
                batch_time = time.time() - batch_start
                
                total_items += len(items)
                batch_count += 1
                
                print(f"\nBatch {batch_count}:")
                print(f"  - Start: {start}, Limit: 50")
                print(f"  - Retrieved: {len(items)} items")
                print(f"  - Time: {batch_time:.2f}s")
                
                if len(items) < 50:
                    print("  - Reached end of library")
                    break
                    
            except Exception as e:
                print(f"\nError in batch {batch_count + 1}: {e}")
                break
        
        total_time = time.time() - start_time
        print(f"\nBatch fetching summary:")
        print(f"  - Total items fetched: {total_items}")
        print(f"  - Total batches: {batch_count}")
        print(f"  - Total time: {total_time:.2f}s")
        print(f"  - Average time per batch: {total_time / batch_count:.2f}s" if batch_count > 0 else "N/A")
        
        # Test 3: Test error handling
        print("\n" + "-" * 50)
        print("\nTest 3: Error handling")
        print("Testing with invalid item key...")
        
        try:
            # This should fail but be handled gracefully
            invalid_item = rate_limited_client.item("INVALID_KEY_12345")
            print("  - Unexpected success!")
        except Exception as e:
            print(f"  - Error handled correctly: {type(e).__name__}")
            print(f"  - Message: {str(e)[:100]}...")
        
        print("\n" + "-" * 50)
        print("Rate limiter tests completed!")
        
    except Exception as e:
        print(f"\nFatal error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rate_limiter()