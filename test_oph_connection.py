#!/usr/bin/env python3
"""
Simple test script to diagnose Ophiuchus server connectivity issues
Run this to test if the server is responding to requests
"""

import socket
import time
import logging
import argparse

def setup_logging(verbose=False):
    """Setup logging based on verbosity level"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

# Server configuration (same as in settings.py)
OPH_SERVER = {
    'host': '100.85.84.122',
    'port': 8002,
    'timeout': 5.0
}

def test_basic_connection(logger):
    """Test basic UDP connectivity to the server"""
    logger.info("Testing basic UDP connection to Ophiuchus server...")
    logger.info(f"Server: {OPH_SERVER['host']}:{OPH_SERVER['port']}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(OPH_SERVER['timeout'])
        
        # Test a few basic requests
        test_requests = ['sc_ra', 'sc_dec', 'sc_az', 'sc_alt', 'mc_curr', 'mc_pos']
        
        for i, request in enumerate(test_requests):
            logger.debug(f"[{i+1}/{len(test_requests)}] Testing request: '{request}'")
            
            try:
                # Send request
                sock.sendto(request.encode('utf-8'), (OPH_SERVER['host'], OPH_SERVER['port']))
                logger.debug(f"Sent request '{request}'")
                
                # Receive response
                data, addr = sock.recvfrom(1024)
                response = data.decode('utf-8').strip()
                logger.debug(f"Response from {addr}: '{response}'")
                
                # Try to parse as number
                try:
                    float_val = float(response)
                    logger.debug(f"Successfully parsed as number: {float_val}")
                except ValueError:
                    logger.debug(f"Could not parse as number, treating as string")
                
                time.sleep(0.1)  # Small delay between requests
                
            except socket.timeout:
                logger.error(f"Timeout waiting for response to '{request}'")
                break
            except Exception as e:
                logger.error(f"Error with request '{request}': {e}")
                break
        
        sock.close()
        logger.debug("Socket closed")
        
    except Exception as e:
        logger.error(f"Failed to create socket or connect: {e}")

def test_all_parameters(logger):
    """Test all parameters that the OphClient would request"""
    from src.data.Oph_client import OphData
    from dataclasses import asdict
    
    logger.info("Testing ALL parameters from OphData...")
    
    # Get all parameter names, excluding 'valid' which is internal
    oph_data = OphData()
    all_fields = asdict(oph_data)
    # Remove 'valid' field - it's internal, not a server parameter
    if 'valid' in all_fields:
        del all_fields['valid']
        logger.debug("Excluded 'valid' field from testing (internal flag only)")
    
    all_params = list(all_fields.keys())
    logger.info(f"Total parameters to test: {len(all_params)}")
    logger.debug(f"Parameters: {all_params}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(OPH_SERVER['timeout'])
        
        successful = 0
        failed = 0
        
        for i, param in enumerate(all_params):
            logger.debug(f"[{i+1}/{len(all_params)}] Testing parameter: '{param}'")
            
            try:
                # Send request
                sock.sendto(param.encode('utf-8'), (OPH_SERVER['host'], OPH_SERVER['port']))
                
                # Receive response
                data, addr = sock.recvfrom(1024)
                response = data.decode('utf-8').strip()
                logger.debug(f"Response: '{response}'")
                
                successful += 1
                time.sleep(0.1)  # Small delay
                
            except socket.timeout:
                logger.debug(f"TIMEOUT for '{param}'")
                failed += 1
            except Exception as e:
                logger.debug(f"ERROR for '{param}': {e}")
                failed += 1
        
        sock.close()
        
        logger.info(f"RESULTS: {successful} successful, {failed} failed out of {len(all_params)} total")
        
        if successful == 0:
            logger.error("NO PARAMETERS WORKING - Server might be down or unreachable")
        elif failed == 0:
            logger.info("ALL PARAMETERS WORKING - Issue might be in client logic")
        else:
            logger.warning(f"PARTIAL SUCCESS - {failed} parameters not responding")
        
    except Exception as e:
        logger.error(f"Failed to test parameters: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Ophiuchus server connectivity')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='Enable verbose output (shows all requests/responses)')
    args = parser.parse_args()
    
    logger = setup_logging(args.verbose)
    
    logger.info("Starting Ophiuchus server connectivity test...")
    if not args.verbose:
        logger.info("Use -v or --verbose for detailed output")
    logger.info("=" * 60)
    
    test_basic_connection(logger)
    
    logger.info("=" * 60)
    
    test_all_parameters(logger)
    
    logger.info("=" * 60)
    logger.info("Test completed!") 