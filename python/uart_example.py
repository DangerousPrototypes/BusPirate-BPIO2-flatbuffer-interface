import argparse
import sys
import time

# Import BPIO client and UART interface
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_uart import BPIOUART

def uart_buffered_mode(client, speed=115200):
    """UART example with buffered async data (read at leisure)."""
    print("=== UART Buffered Mode Example ===\n")
    
    uart = BPIOUART(client)

    # Configure UART without callback - data accumulates in buffer
    print("Configuring UART interface (buffered mode)...\n")
    if uart.configure(speed=speed, data_bits=8, parity=False, stop_bits=1, 
                      psu_enable=True, psu_set_mv=3300, psu_set_ma=0):

        print(f"UART configured at {speed} baud\n")
        
        # Send test message
        print("Sending test message...")
        test_message = b"Hello UART!\r\n"
        response = uart.write(test_message)
        if response:
            print(f"TX: {test_message.hex()} ({test_message})")
        
        # Wait for async loopback data to accumulate
        print("Waiting for async loopback data (3 seconds)...\n")
        time.sleep(3)
        
        # Read buffered async data at our leisure
        async_data = uart.read_async()
        if async_data:
            print(f"Async RX (buffered): {async_data.hex()} ({async_data})")
        else:
            print("No async data received")
        
        print("\nBuffered mode test complete.")
    else:
        print("Failed to configure UART interface")
        return False
    
    return True

def uart_callback_mode(client, speed=115200):
    """UART example with callback for real-time async data processing."""
    print("=== UART Callback Mode Example ===\n")
    
    uart = BPIOUART(client)
    
    # Track received data
    received_chunks = []
    
    def async_data_handler(data):
        """Callback function called when async data arrives"""
        print(f"  Callback RX: {data.hex()} ({data})")
        received_chunks.append(data)
    
    # Configure UART with callback - data goes directly to handler
    print("Configuring UART interface (callback mode)...\n")
    if uart.configure(speed=speed, data_bits=8, parity=False, stop_bits=1,
                      psu_enable=True, psu_set_mv=3300, psu_set_ma=0,
                      async_callback=async_data_handler):
        
        print(f"UART configured at {speed} baud\n")
        
        # Send test message
        print("Sending test message...")
        test_message = b"Hello UART!\r\n"
        response = uart.write(test_message)
        if response:
            print(f"TX: {test_message.hex()} ({test_message})")
        
        # Wait for async loopback data (handler called automatically)
        print("\nWaiting for async loopback (callback will be called)...\n")
        time.sleep(3)
        
        # Show what was received via callback
        if received_chunks:
            total_data = b''.join(received_chunks)
            print(f"\nTotal received via callback: {total_data.hex()} ({total_data})")
            print(f"Received in {len(received_chunks)} chunks")
        else:
            print("\nNo async data received")
        
        print("\nCallback mode test complete.")
    else:
        print("Failed to configure UART interface")
        return False
    
    return True
        

# Example usage and testing
def main():
    """Example UART usage with async monitoring"""

    parser = argparse.ArgumentParser(
        description='BPIO2 UART Example - Demonstrates buffered and callback async modes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -p COM3                    # Run callback mode example (default)
    %(prog)s -p COM3 --mode buffered    # Run buffered mode example
    %(prog)s -p COM3 --speed 9600       # Use 9600 baud with callback mode

Async Modes:
    Callback Mode (default):
        - Provide a callback function to configure()
        - Callback is called immediately when async data arrives
        - Good for real-time processing and event-driven applications
        - Data is NOT buffered when using callback mode
        
    Buffered Mode:
        - Async data accumulates in an internal buffer
        - Read at your leisure with uart.read_async()
        - Good for polling-based applications
"""
    )
    parser.add_argument('-p', '--port', required=True,
                       help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--speed', type=int, default=115200,
                       help='UART speed in bps (default: 115200)')
    parser.add_argument('--mode', choices=['buffered', 'callback'], default='callback',
                       help='Which mode to demonstrate (default: callback)')
    
    args = parser.parse_args()
    
    try:
        client = BPIOClient(args.port)
        print(f"Connected to Bus Pirate on {args.port}\n")

        if args.mode == 'buffered':
            success = uart_buffered_mode(client, speed=args.speed)
        else:  # callback
            success = uart_callback_mode(client, speed=args.speed)
        
        return 0 if success else 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())