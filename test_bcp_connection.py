#!/usr/bin/env python3
"""
BCP Spectrometer Connection Test Script
Run this to verify that the BCP spectrometer server is working when you turn it back on.
"""

import sys
import time
import logging
sys.path.insert(0, 'src')

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from data.bcp_spectrometer_client import BCPSpectrometerClient

def test_bcp_connection():
    """Test BCP spectrometer connection and data retrieval"""
    print("🔍 BCP Spectrometer Connection Test")
    print("=" * 50)
    
    client = BCPSpectrometerClient()
    print(f"📡 Testing connection to: {client.server_ip}:{client.server_port}")
    print(f"⏱️  Timeout: {client.timeout}s")
    print()
    
    # Test connection with 3 attempts
    for attempt in range(1, 4):
        print(f"Attempt {attempt}/3: Getting spectrum data...")
        
        start_time = time.time()
        spectrum_data = client.get_spectrum()
        elapsed = time.time() - start_time
        
        if spectrum_data and spectrum_data.valid and len(spectrum_data.data) > 0:
            print(f"✅ SUCCESS! Connection established in {elapsed:.2f}s")
            print(f"   📊 Spectrum Type: {spectrum_data.type}")
            print(f"   📈 Data Points: {spectrum_data.points}")
            print(f"   🔢 Sample Values: {spectrum_data.data[:3]}...")
            if hasattr(spectrum_data, 'freq_start') and spectrum_data.freq_start:
                print(f"   📡 Frequency Range: {spectrum_data.freq_start:.3f} - {spectrum_data.freq_end:.3f} GHz")
            print()
            return True
        else:
            print(f"❌ FAILED in {elapsed:.2f}s")
            if spectrum_data:
                print(f"   Error Type: {spectrum_data.type}")
                print(f"   Valid: {spectrum_data.valid}")
            else:
                print("   No response from server")
            print()
        
        if attempt < 3:
            print("   Waiting 2 seconds before retry...")
            time.sleep(2)
    
    print("❌ All connection attempts failed.")
    print()
    print("💡 Troubleshooting:")
    print("   1. Make sure the BCP spectrometer server is running on Sag")
    print("   2. Check network connectivity to 100.70.234.8")
    print("   3. Verify the server is listening on port 8081") 
    print("   4. Check if your IP is authorized in the BCP server config")
    return False

if __name__ == "__main__":
    success = test_bcp_connection()
    sys.exit(0 if success else 1) 