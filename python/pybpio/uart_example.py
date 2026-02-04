#!/usr/bin/env python3
"""
UART BPIO Example for Bus Pirate 5

This example demonstrates how to use the UART BPIO interface for both 
synchronous transactions and asynchronous data monitoring.

Requirements:
- Bus Pirate 5 with BPIO2 firmware
- Python 3.6+
- pybpio library from BusPirate-BPIO2-flatbuffer-interface repository

Usage:
    python uart_example.py -p <port> [options]

Examples:
    uart_example.py -p COM3                           # Basic UART test
    uart_example.py -p /dev/ttyUSB0 --speed 9600      # Different baud rate  
    uart_example.py -p COM3 --loopback                # Loopback test
    uart_example.py -p COM3 --monitor-only            # Just monitor async data
"""

import argparse
import sys
import time
import threading
from pathlib import Path

# Add the python library to path (adjust as needed for your setup)
sys.path.append('python')
sys.path.append('python/pybpio')

try:
    from pybpio.bpio_client import BPIOClient
    from pybpio.bpio_uart import BPIOUART
except ImportError as e:
    print(f"Error importing pybpio library: {e}")
    print("Please ensure the pybpio library is in your Python path")
    print("Download from: https://github.com/DangerousPrototypes/BusPirate-BPIO2-flatbuffer-interface")
    sys.exit(1)

def setup_uart(client, args):
    """Setup and configure UART mode"""
    uart = BPIOUART(client)
    
    print(f"Configuring UART:")
    print(f"  Speed: {args.speed} baud")
    print(f"  Data bits: {args.data_bits}")
    print(f"  Parity: {'Even' if args.parity else 'None'}")
    print(f"  Stop bits: {args.stop_bits}")
    print(f"  Flow control: {'Yes' if args.flow_control else 'No'}")
    print(f"  Signal inversion: {'Yes' if args.signal_inversion else 'No'}")
    
    if not uart.configure(
        speed=args.speed,
        data_bits=args.data_bits,
        parity=args.parity,
        stop_bits=args.stop_bits,
        flow_control=args.flow_control,
        signal_inversion=args.signal_inversion
    ):
        print("ERROR: Failed to configure UART")
        return None
    
    print("UART configured successfully!")
    return uart

def async_data_handler(data):
    """Handle asynchronous UART data"""
    try:
        # Try to decode as text, fall back to hex
        try:
            text = data.decode('utf-8', errors='ignore')
            if text.isprintable():
                print(f"Async RX: '{text.strip()}' ({len(data)} bytes)")
            else:
                print(f"Async RX: {data.hex()} ({len(data)} bytes)")
        except:
            print(f"Async RX: {data.hex()} ({len(data)} bytes)")
    except Exception as e:
        print(f"Error in async handler: {e}")

def loopback_test(uart, args):
    """Perform loopback test"""
    print("\n=== LOOPBACK TEST ===")
    print("Connect TX to RX for this test")
    print("Press Ctrl+C to stop\n")
    
    test_messages = [
        b"Hello World!\r\n",
        b"Test message 123\r\n", 
        b"UART BPIO Test\r\n",
        b"\x01\x02\x03\x04\x05"  # Binary data
    ]
    
    try:
        for i, message in enumerate(test_messages):
            print(f"Test {i+1}: Sending {len(message)} bytes...")
            
            # Send data
            response = uart.write(message)
            if not response:
                print("  ERROR: Write failed")
                continue
                
            print(f"  TX: {message} ({message.hex()})")
            
            # Read back the same amount
            time.sleep(0.1)  # Give time for loopback
            response = uart.read(len(message))
            
            if response and 'data_read' in response:
                received = bytes(response['data_read'])
                print(f"  RX: {received} ({received.hex()})")
                
                if received == message:
                    print("  ✓ PASS: Data matches")
                else:
                    print("  ✗ FAIL: Data mismatch")
            else:
                print("  ERROR: Read failed or no data")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nLoopback test interrupted")

def interactive_test(uart, args):
    """Interactive UART test"""
    print("\n=== INTERACTIVE TEST ===")
    print("Type messages to send (empty line to quit)")
    print("Async data will be displayed as received\n")
    
    try:
        while True:
            try:
                user_input = input("TX> ").strip()
                if not user_input:
                    break
                    
                # Add line ending if not present
                message = user_input.encode('utf-8')
                if not message.endswith(b'\r\n') and not message.endswith(b'\n'):
                    message += b'\r\n'
                
                # Send the message
                response = uart.write(message)
                if response:
                    print(f"Sent: {len(message)} bytes")
                else:
                    print("ERROR: Send failed")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
                
    except Exception as e:
        print(f"Interactive test error: {e}")

def monitor_only_test(uart, args):
    """Just monitor for async data"""
    print("\n=== MONITORING MODE ===")
    print("Listening for UART data...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

def main():
    parser = argparse.ArgumentParser(
        description='UART BPIO Example - Test UART interface with async support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p COM3                           # Basic UART test
  %(prog)s -p /dev/ttyUSB0 --speed 9600      # Different baud rate  
  %(prog)s -p COM3 --loopback                # Loopback test
  %(prog)s -p COM3 --monitor-only            # Just monitor async data
  %(prog)s -p COM3 --parity --stop-bits 2    # Different settings
        """)
    
    parser.add_argument('-p', '--port', required=True,
                        help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--speed', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    parser.add_argument('--data-bits', type=int, default=8, choices=[5,6,7,8],
                        help='Data bits (default: 8)')
    parser.add_argument('--parity', action='store_true',
                        help='Enable even parity (default: no parity)')
    parser.add_argument('--stop-bits', type=int, default=1, choices=[1,2],
                        help='Stop bits (default: 1)')
    parser.add_argument('--flow-control', action='store_true',
                        help='Enable hardware flow control')
    parser.add_argument('--signal-inversion', action='store_true',
                        help='Invert UART signals')
    parser.add_argument('--loopback', action='store_true',
                        help='Run loopback test')
    parser.add_argument('--monitor-only', action='store_true',
                        help='Only monitor for async data')
    parser.add_argument('--no-async', action='store_true',
                        help='Disable async monitoring')
    
    args = parser.parse_args()
    
    try:
        print(f"Connecting to Bus Pirate on {args.port}...")
        client = BPIOClient(args.port)
        
        # Show Bus Pirate status
        print("\n=== BUS PIRATE STATUS ===")
        client.show_status()
        
        # Setup UART
        uart = setup_uart(client, args)
        if not uart:
            return 1
        
        # Start async monitoring unless disabled
        if not args.no_async:
            print("\nStarting async data monitoring...")
            uart.start_async_monitoring(callback=async_data_handler)
        
        # Run the appropriate test
        if args.monitor_only:
            monitor_only_test(uart, args)
        elif args.loopback:
            loopback_test(uart, args)
        else:
            interactive_test(uart, args)
        
        # Clean up
        if not args.no_async:
            print("\nStopping async monitoring...")
            uart.stop_async_monitoring()
            
            # Get any buffered data
            buffered_data = uart.get_async_data()
            if buffered_data:
                print(f"Retrieved {len(buffered_data)} buffered async packets")
        
        print("UART example complete.")
        return 0
        
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    sys.exit(main())