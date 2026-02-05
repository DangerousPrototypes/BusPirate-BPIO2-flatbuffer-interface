#!/usr/bin/env python3
"""
BPIO2 SPI Example - Read flash memory JEDEC ID
Demonstrates basic SPI communication with flash memory devices.
"""

import argparse
import sys

# Import BPIO client and SPI interface
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_spi import BPIOSPI

def spi_read_jedec_id(client, speed=1000000):
    """Read JEDEC ID from SPI flash memory."""
    spi = BPIOSPI(client)
    
    if spi.configure(speed=speed, clock_polarity=False, clock_phase=False, 
                    chip_select_idle=True, psu_enable=True, psu_set_mv=3300, 
                    psu_set_ma=0, pullup_enable=True):
        
        print(f"SPI configured at {speed/1000000:.1f}MHz")
        
        # Read JEDEC ID (0x9F command)
        print("Reading SPI flash JEDEC ID...")
        data = spi.transfer(write_data=[0x9F], read_bytes=3)
        
        if data and len(data) == 3:
            manufacturer = data[0]
            device_type = data[1]
            capacity = data[2]
            
            print(f"JEDEC ID: {data.hex().upper()}")
            print(f"Manufacturer ID: 0x{manufacturer:02X}")
            print(f"Device Type: 0x{device_type:02X}")
            print(f"Capacity: 0x{capacity:02X}")
            
            # Decode common manufacturers
            manufacturers = {
                0xEF: "Winbond",
                0xC2: "Macronix", 
                0x20: "Micron/ST",
                0x01: "Spansion/Cypress",
                0xBF: "SST/Microchip",
                0x1F: "Atmel/Adesto",
                0x85: "Puya"
            }
            
            if manufacturer in manufacturers:
                print(f"Manufacturer: {manufacturers[manufacturer]}")
            else:
                print(f"Manufacturer: Unknown (0x{manufacturer:02X})")
                
        else:
            print("Failed to read JEDEC ID")
            return False
    else:
        print("Failed to configure SPI interface")
        return False
    
    return True

def spi_read_status(client, speed=1000000):
    """Read status register from SPI flash."""
    spi = BPIOSPI(client)
    
    if spi.configure(speed=speed, clock_polarity=False, clock_phase=False,
                    chip_select_idle=True, psu_enable=True, psu_set_mv=3300,
                    psu_set_ma=0, pullup_enable=True):
        
        print("Reading SPI flash status register...")
        data = spi.transfer(write_data=[0x05], read_bytes=1)
        
        if data and len(data) == 1:
            status = data[0]
            print(f"Status Register: 0x{status:02X} (0b{status:08b})")
            print(f"  WIP (Write in Progress): {'Yes' if status & 0x01 else 'No'}")
            print(f"  WEL (Write Enable Latch): {'Yes' if status & 0x02 else 'No'}")
            print(f"  Block Protection bits: 0b{(status >> 2) & 0x07:03b}")
            return True
        else:
            print("Failed to read status register")
            return False
    else:
        print("Failed to configure SPI interface")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='BPIO2 SPI Example - Communicate with SPI flash memory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p COM3                    # Read JEDEC ID at 1MHz
  %(prog)s -p COM3 --speed 10000000   # Read JEDEC ID at 10MHz  
  %(prog)s -p COM3 --status           # Read status register
        """
    )
    
    parser.add_argument('-p', '--port', required=True,
                       help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--speed', type=int, default=1000000,
                       help='SPI clock speed in Hz (default: 1000000)')
    parser.add_argument('--status', action='store_true',
                       help='Read status register instead of JEDEC ID')
    
    args = parser.parse_args()
    
    try:
        client = BPIOClient(args.port)
        print(f"Connected to Bus Pirate on {args.port}")
        
        if args.status:
            success = spi_read_status(client, args.speed)
        else:
            success = spi_read_jedec_id(client, args.speed)
        
        client.close()
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())