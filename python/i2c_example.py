#!/usr/bin/env python3
"""
BPIO2 I2C Example - Read from 24x02 EEPROM
Demonstrates basic I2C communication with configuration options.
"""

import argparse
import sys

# Import BPIO client and I2C interface
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_i2c import BPIOI2C

def i2c_scan_example(client):
    """I2C Scan example with status display."""
    i2c = BPIOI2C(client)
    # Configure I2C with all hardware settings
    print("Configuring I2C interface...\n")
    if i2c.configure(speed=100000, pullup_enable=True, psu_enable=True, 
                    psu_set_mv=3300, psu_set_ma=0):
        
        Found=i2c.scan()
        # Print as hex
        print("I2C Scan Results (Hex):")
        for addr in Found:
            print(f"0x{addr:02X}", end=' ')

def i2c_basic_example(client, device_addr=0xA0, register_addr=0x00, read_bytes=8):
    """Basic I2C read example with status display."""
    i2c = BPIOI2C(client)
    
    # Configure I2C with all hardware settings
    print("Configuring I2C interface...\n")
    if i2c.configure(speed=400000, pullup_enable=True, psu_enable=True, 
                    psu_set_mv=3300, psu_set_ma=0):
        
        # Show configuration with individual setters (less efficient but demonstrates API)
        # Display status information
        print(f"Current mode: {i2c.get_mode_current()}")
        print(f"PSU enabled: {i2c.get_psu_enabled()}")
        print(f"PSU voltage: {i2c.get_psu_measured_mv()}mV")
        print(f"PSU current: {i2c.get_psu_measured_ma()}mA")
        print(f"Pull-up enabled: {i2c.get_pullup_enabled()}")
        
        # Perform I2C read
        print(f"\nReading {read_bytes} bytes from device 0x{device_addr:02X}, register 0x{register_addr:02X}...")
        data = i2c.transfer(write_data=[device_addr, register_addr], read_bytes=read_bytes)
        
        if data:
            print(f"Read data: {data.hex()}")
            print(f"Read data (hex): {' '.join(f'{b:02X}' for b in data)}")
        else:
            print("Failed to read data from I2C device")
            return False
    else:
        print("Failed to configure I2C interface")
        return False
    
    return True

def i2c_eeprom_dump(client, device_addr=0xA0, size=256):
    """Read entire EEPROM contents."""
    i2c = BPIOI2C(client)
    
    if i2c.configure(speed=400000, pullup_enable=True, psu_enable=True, 
                    psu_set_mv=3300, psu_set_ma=0):
        
        print(f"Reading {size} bytes from EEPROM at 0x{device_addr:02X}...")
        data = i2c.transfer(write_data=[device_addr, 0x00], read_bytes=size)
        
        if data:
            print(f"EEPROM dump ({len(data)} bytes):")
            # Print in hex dump format
            for i in range(0, len(data), 16):
                addr = i
                hex_part = ' '.join(f'{data[j]:02X}' for j in range(i, min(i+16, len(data))))
                ascii_part = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' 
                                   for j in range(i, min(i+16, len(data))))
                print(f"{addr:04X}: {hex_part:<47} {ascii_part}")
        else:
            print("Failed to read EEPROM data")
            return False
    else:
        print("Failed to configure I2C interface")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='BPIO2 I2C Example -Read from 24x02 EEPROM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p COM3                           # Basic read from default EEPROM
  %(prog)s -p COM3 --device 0x50             # Read from device at 0x50
  %(prog)s -p COM3 --register 0x10 --bytes 4 # Read 4 bytes from register 0x10
        """
    )
    
    parser.add_argument('-p', '--port', required=True,
                       help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--device', type=lambda x: int(x, 0), default=0xA0,
                       help='I2C device address (default: 0xA0)')
    parser.add_argument('--register', type=lambda x: int(x, 0), default=0x00,
                       help='Register address to read from (default: 0x00)')
    parser.add_argument('--bytes', type=int, default=8,
                       help='Number of bytes to read (default: 8)')
    parser.add_argument('--dump', action='store_true',
                       help='Dump entire EEPROM contents')
    
    args = parser.parse_args()
    
    try:
        client = BPIOClient(args.port)
        print(f"Connected to Bus Pirate on {args.port}")
        
        if args.dump:
            # read all 256 bytes from 24x02 EEPROM
            success = i2c_eeprom_dump(client, args.device, 256)
        else:
            success = i2c_basic_example(client, args.device, args.register, args.bytes)
        
        client.close()
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())