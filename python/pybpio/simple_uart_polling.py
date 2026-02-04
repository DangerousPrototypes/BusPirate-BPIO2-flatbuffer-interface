#!/usr/bin/env python3
"""
Simple UART BPIO Polling Example

This example demonstrates simple polling for UART data using the new async 
feature. It shows the minimal code needed to send/receive UART data and 
poll for unsolicited incoming data.

Usage:
    python simple_uart_polling.py <port>

Example:
    python simple_uart_polling.py COM3
    python simple_uart_polling.py /dev/ttyUSB0
"""

import sys
import time

# Add the python library to path (adjust as needed for your setup)
sys.path.append('python')
sys.path.append('python/pybpio')

try:
    from pybpio.bpio_client import BPIOClient
    from pybpio.bpio_uart import BPIOUART
except ImportError:
    print("Error: pybpio library not found")
    print("Download from: https://github.com/DangerousPrototypes/BusPirate-BPIO2-flatbuffer-interface")
    sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_uart_polling.py <port>")
        print("Example: python simple_uart_polling.py COM3")
        sys.exit(1)
    
    port = sys.argv[1]
    
    try:
        # Connect and configure
        print(f"Connecting to {port}...")
        client = BPIOClient(port)
        uart = BPIOUART(client)
        
        print("Configuring UART (115200, 8N1)...")
        uart.configure(speed=115200, data_bits=8, parity=False, stop_bits=1)
        
        # Send a test message
        print("Sending test message...")
        test_msg = b"Hello UART World!\r\n"
        uart.write(test_msg)
        print(f"Sent: {test_msg}")
        
        # Simple polling loop
        print("Polling for UART data for 30 seconds...")
        print("Send data to see async reception...")
        
        start_time = time.time()
        while (time.time() - start_time) < 30:
            # Check for async data using the client's async check
            # This is the key new feature - async data detection!
            async_response = client.check_async_data(timeout=0.1)
            
            if async_response and async_response.get('is_async', False):
                data = async_response.get('data_read', [])
                if data:
                    received = bytes(data)
                    try:
                        # Try to decode as text
                        text = received.decode('utf-8', errors='ignore')
                        print(f"Async RX: '{text.strip()}' ({len(received)} bytes)")
                    except:
                        # Fall back to hex
                        print(f"Async RX: {received.hex()} ({len(received)} bytes)")
            
            # Small delay to prevent excessive polling
            time.sleep(0.05)
        
        print("Polling complete!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    main()