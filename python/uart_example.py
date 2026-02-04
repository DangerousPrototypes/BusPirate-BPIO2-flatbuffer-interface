import argparse
import sys
import time

# Import BPIO client and SPI interface
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_uart import BPIOUART

def uart_async_example(client, speed=115200):
    """UART example with asynchronous data monitoring."""

    uart = BPIOUART(client)

    # Configure UART with all hardware settings
    print("Configuring UART interface...\n")
    if uart.configure(speed=speed, data_bits=8, parity=False, stop_bits=1):

        print(f"UART configured at {speed} baud\n")
                
        # Define callback for async data
        def async_data_callback(data):
            print(f"Async RX: {data.hex()} ({data})")
        
        # Start async monitoring
        print("Starting async monitoring...")
        uart.start_async_monitoring(callback=async_data_callback)
        
        # Send some test data
        print("Sending test message...")
        test_message = b"Hello UART!\r\n"
        response = uart.write(test_message)
        if response:
            print(f"TX: {test_message.hex()} ({test_message})")
        
        # Read some data
        print("Reading 10 bytes...")
        response = uart.read(10)
        if response and 'data_read' in response:
            data = bytes(response['data_read'])
            print(f"RX: {data.hex()} ({data})")
        """
        # Monitor for async data for 10 seconds
        print("Monitoring for async data for 10 seconds...")
        time.sleep(10)
        
        # Get any buffered data
        buffered_data = uart.get_async_data()
        if buffered_data:
            print(f"Buffered async data: {len(buffered_data)} packets")
            for i, data in enumerate(buffered_data):
                print(f"  Packet {i}: {data.hex()} ({data})")
        
        # Stop async monitoring
        uart.stop_async_monitoring()
        """
        print("UART test complete.")
    else:
        print("Failed to configure UART interface")
        return False
    
    return True
        

# Example usage and testing
def main():
    """Example UART usage with async monitoring"""

    parser = argparse.ArgumentParser(
        description='BPIO2 UART Example - UART with asynchronous data monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -p COM3                    # UART async example at 115200 bps
    %(prog)s -p COM3 --speed 9600       # UART async example at 9600 bps
"""
    )
    parser.add_argument('-p', '--port', required=True,
                       help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--speed', type=int, default=115200,
                       help='UART speed in bps (default: 115200)')
    
    args = parser.parse_args()
    try:
        client = BPIOClient(args.port)
        print(f"Connected to Bus Pirate on {args.port}")

        success = uart_async_example(client, speed=args.speed)
        return 0 if success else 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())