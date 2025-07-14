#!/usr/bin/env python3
"""
Debug script for PR59 server connectivity
Tests different IP addresses and provides detailed connection info
"""

import socket
import sys

def test_connection(host, port, timeout=2.0):
    """Test basic UDP connection to server"""
    print(f"\nTesting connection to {host}:{port}...")
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Send a test request
        test_channel = "pr59_temp"
        request = test_channel.encode('utf-8')
        
        print(f"  Sending request: '{test_channel}'")
        sock.sendto(request, (host, port))
        
        # Try to receive response
        response, addr = sock.recvfrom(1024)
        sock.close()
        
        response_str = response.decode('utf-8').strip()
        print(f"  ✅ SUCCESS! Response: '{response_str}' from {addr}")
        return True, response_str
        
    except socket.timeout:
        print(f"  ❌ TIMEOUT - No response within {timeout}s")
        return False, "TIMEOUT"
    except socket.gaierror as e:
        print(f"  ❌ DNS ERROR: {e}")
        return False, f"DNS_ERROR: {e}"
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False, f"ERROR: {e}"
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    """Test various connection configurations"""
    print("PR59 Server Connection Debug Tool")
    print("=" * 50)
    
    # Test configurations
    configs = [
        ("127.0.0.1", 8082),     # Localhost
        ("localhost", 8082),     # Localhost via hostname
        ("100.70.234.8", 8082),  # BCP Spectrometer IP (from settings)
        ("100.85.84.122", 8082), # Ophiuchus IP (from settings)
    ]
    
    successful_configs = []
    
    for host, port in configs:
        success, response = test_connection(host, port, timeout=3.0)
        if success:
            successful_configs.append((host, port, response))
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    if successful_configs:
        print(f"✅ Found {len(successful_configs)} working configuration(s):")
        for host, port, response in successful_configs:
            print(f"   {host}:{port} -> {response}")
        
        # Test all PR59 channels with first working config
        if successful_configs:
            host, port, _ = successful_configs[0]
            print(f"\nTesting all PR59 channels with {host}:{port}:")
            
            channels = [
                "pr59_kp", "pr59_ki", "pr59_kd", "pr59_timestamp",
                "pr59_temp", "pr59_fet_temp", "pr59_current", 
                "pr59_voltage", "pr59_power", "pr59_running", "pr59_status"
            ]
            
            for channel in channels:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(2.0)
                    
                    request = channel.encode('utf-8')
                    sock.sendto(request, (host, port))
                    
                    response, addr = sock.recvfrom(1024)
                    response_str = response.decode('utf-8').strip()
                    
                    print(f"  {channel:15}: {response_str}")
                    sock.close()
                    
                except Exception as e:
                    print(f"  {channel:15}: ERROR - {e}")
                    try:
                        sock.close()
                    except:
                        pass
    else:
        print("❌ No working configurations found!")
        print("\nPossible issues:")
        print("  1. PR59 server is not running")
        print("  2. Server is running on a different IP/port")
        print("  3. Firewall is blocking connections")
        print("  4. Server is using TCP instead of UDP")
        
        print("\nTo check if server is running:")
        print("  netstat -an | grep 8082")
        print("  lsof -i :8082")

if __name__ == "__main__":
    main() 