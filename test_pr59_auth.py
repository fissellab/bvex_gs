#!/usr/bin/env python3
"""
Test different authentication methods for PR59 server
"""

import socket
import sys

def test_request_format(host, port, request_data, description):
    """Test a specific request format"""
    print(f"\nTesting: {description}")
    print(f"  Request: {repr(request_data)}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        
        if isinstance(request_data, str):
            request = request_data.encode('utf-8')
        else:
            request = request_data
            
        sock.sendto(request, (host, port))
        response, addr = sock.recvfrom(1024)
        sock.close()
        
        response_str = response.decode('utf-8').strip()
        print(f"  ✅ Response: '{response_str}'")
        return True, response_str
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, str(e)
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    """Test various request formats"""
    host = "100.70.234.8"
    port = 8082
    
    print(f"Testing PR59 Authentication Methods on {host}:{port}")
    print("=" * 60)
    
    # Test various request formats
    test_cases = [
        # Basic channel requests
        ("pr59_temp", "Basic channel request"),
        
        # Try with authentication keywords
        ("AUTH pr59_temp", "With AUTH prefix"),
        ("LOGIN pr59_temp", "With LOGIN prefix"),
        ("GET pr59_temp", "With GET prefix"),
        ("QUERY pr59_temp", "With QUERY prefix"),
        
        # Try with formatting like other protocols
        ("GET_PR59:pr59_temp", "GET_PR59 format"),
        ("PR59:pr59_temp", "PR59 prefix format"),
        ("TELEMETRY:pr59_temp", "TELEMETRY prefix"),
        
        # Try specific authentication tokens/passwords
        ("admin pr59_temp", "With admin credential"),
        ("bvex pr59_temp", "With bvex credential"),
        ("pr59 pr59_temp", "With pr59 credential"),
        
        # Try binary formats
        (b"\x01pr59_temp", "Binary prefix \\x01"),
        (b"\x00pr59_temp", "Binary prefix \\x00"),
        
        # Try JSON-like format
        ('{"channel": "pr59_temp"}', "JSON format"),
        
        # Try simple authentication
        ("user:bvex\npr59_temp", "User authentication"),
        ("token:123\npr59_temp", "Token authentication"),
    ]
    
    successful = []
    
    for request, description in test_cases:
        success, response = test_request_format(host, port, request, description)
        if success and "ERROR:UNAUTHORIZED" not in response:
            successful.append((request, response, description))
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    
    if successful:
        print(f"✅ Found {len(successful)} working format(s):")
        for request, response, description in successful:
            print(f"   {description}: {repr(request)} -> {response}")
    else:
        print("❌ No working authentication method found")
        print("\nAll requests returned UNAUTHORIZED or failed.")
        print("The server may require:")
        print("  1. Specific client IP authentication")
        print("  2. Certificate-based authentication")
        print("  3. A different protocol (TCP instead of UDP)")
        print("  4. Server-side authorization configuration")

if __name__ == "__main__":
    main() 