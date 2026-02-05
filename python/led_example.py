import argparse
import sys
import time

# Import BPIO client and LED interface
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_led import BPIOLED

def test_ws2812(client):
    """Test WS2812 external LED strip"""
    print("=== WS2812 External LED Test ===\n")
    
    led = BPIOLED(client)
    
    # Configure for WS2812
    print("Configuring for WS2812 external LEDs...\n")
    if not led.configure(led_type='WS2812', psu_enable=True, psu_set_mv=5000, psu_set_ma=0):
        print("Failed to configure WS2812")
        return False
    
    print("WS2812 configured\n")
    
    # Cycle through colors on first LED
    colors = [
        (255, 0, 0, "Red"),
        (0, 255, 0, "Green"),
        (0, 0, 255, "Blue"),
        (255, 255, 0, "Yellow"),
        (255, 0, 255, "Magenta"),
        (0, 255, 255, "Cyan"),
        (255, 255, 255, "White"),
    ]
    
    for r, g, b, name in colors:
        print(f"Setting LED to {name} (R={r}, G={g}, B={b})")
        led.set_rgb(r, g, b)
        time.sleep(0.5)
    
    # Test multiple LEDs (rainbow on 5 LEDs)
    print("\nSetting rainbow pattern on 5 LEDs...")
    rainbow = [
        (255, 0, 0),    # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
    ]
    led.set_multiple_rgb(rainbow)
    time.sleep(1)
    
    # Clear LEDs
    print("Clearing LEDs...")
    led.clear(num_leds=5)
    
    print("\nWS2812 test complete.\n")
    return True

def test_apa102(client):
    """Test APA102 LED strip"""
    print("=== APA102 LED Test ===\n")
    
    led = BPIOLED(client)
    
    # Configure for APA102
    print("Configuring for APA102 LEDs...\n")
    if not led.configure(led_type='APA102', psu_enable=True, psu_set_mv=5000, psu_set_ma=0):
        print("Failed to configure APA102")
        return False
    
    print("APA102 configured\n")
    
    # Test brightness levels with red
    print("Testing brightness levels (red)...")
    for brightness in [31, 15, 7, 3, 1]:
        print(f"  Brightness: {brightness}/31")
        led.set_rgb(255, 0, 0, brightness=brightness)
        time.sleep(0.5)
    
    # Cycle through colors at full brightness
    colors = [
        (255, 0, 0, "Red"),
        (0, 255, 0, "Green"),
        (0, 0, 255, "Blue"),
        (255, 255, 255, "White"),
    ]
    
    print("\nCycling through colors (full brightness)...")
    for r, g, b, name in colors:
        print(f"  {name}")
        led.set_rgb(r, g, b, brightness=31)
        time.sleep(0.5)
    
    # Test multiple LEDs with different brightness levels
    print("\nSetting gradient on 4 LEDs (varying brightness)...")
    gradient = [
        (255, 0, 0),    # Red
        (255, 64, 0),   # Red-Orange
        (255, 128, 0),  # Orange
        (255, 255, 0),  # Yellow
    ]
    led.set_multiple_rgb(gradient, brightness=15)
    time.sleep(1)
    
    # Same gradient at full brightness
    print("Same gradient at full brightness...")
    led.set_multiple_rgb(gradient, brightness=31)
    time.sleep(1)
    
    # Clear LEDs
    print("Clearing LEDs...")
    led.clear(num_leds=4)
    
    print("\nAPA102 test complete.\n")
    return True

def test_onboard(client):
    """Test onboard RGB LED"""
    print("=== Onboard RGB LED Test ===\n")
    
    led = BPIOLED(client)
    
    # Configure for onboard LED
    print("Configuring for onboard RGB LED...\n")
    if not led.configure(led_type='ONBOARD'):
        print("Failed to configure onboard LED")
        return False
    
    print("Onboard LED configured\n")
    
    # Cycle through colors
    colors = [
        (255, 0, 0, "Red"),
        (0, 255, 0, "Green"),
        (0, 0, 255, "Blue"),
        (255, 255, 0, "Yellow"),
        (255, 0, 255, "Magenta"),
        (0, 255, 255, "Cyan"),
        (255, 255, 255, "White"),
        (128, 128, 128, "Gray"),
    ]
    
    for r, g, b, name in colors:
        print(f"Setting onboard LED to {name} (R={r}, G={g}, B={b})")
        led.set_rgb(r, g, b)
        time.sleep(2)
    
    # Breathing effect (fade red in and out)
    print("\nBreathing effect (red)...")
    for _ in range(2):
        # Fade in
        for brightness in range(0, 256, 16):
            led.set_rgb(brightness, 0, 0)
            time.sleep(0.05)
        # Fade out
        for brightness in range(255, -1, -16):
            led.set_rgb(brightness, 0, 0)
            time.sleep(0.05)
    
    # Turn off
    print("Turning off onboard LED...")
    led.set_rgb(0, 0, 0)
    
    print("\nOnboard LED test complete.\n")
    return True

def main():
    """LED example demonstrating all three LED types"""
    
    parser = argparse.ArgumentParser(
        description='BPIO2 LED Example - Demonstrates WS2812, APA102, and Onboard RGB LEDs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s -p COM3                      # Test onboard RGB LED (default)
    %(prog)s -p COM3 --type ws2812        # Test WS2812 external LEDs
    %(prog)s -p COM3 --type apa102        # Test APA102 external LEDs
    %(prog)s -p COM3 --type all           # Test all LED types

LED Types:
    onboard (default):
        - Built-in RGB LED on Bus Pirate
        - Single addressable LED
        - No external wiring needed
        
    ws2812:
        - WS2812/WS2812B/NeoPixel compatible
        - External LED strip/ring required
        - Data wire to SDO pin
        - Supports multiple LEDs in chain
        
    apa102:
        - APA102/DotStar compatible
        - External LED strip required  
        - Data wire to MOSI, Clock to CLK
        - Supports multiple LEDs and brightness control
"""
    )
    parser.add_argument('-p', '--port', required=True,
                       help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--type', choices=['onboard', 'ws2812', 'apa102', 'all'], 
                       default='onboard',
                       help='LED type to test (default: onboard)')
    
    args = parser.parse_args()
    
    try:
        client = BPIOClient(args.port)
        print(f"Connected to Bus Pirate on {args.port}\n")
        
        success = True
        
        if args.type == 'onboard' or args.type == 'all':
            success = test_onboard(client)
            if args.type == 'all' and success:
                print("=" * 50 + "\n")
        
        if args.type == 'ws2812' or (args.type == 'all' and success):
            success = test_ws2812(client)
            if args.type == 'all' and success:
                print("=" * 50 + "\n")
        
        if args.type == 'apa102' or (args.type == 'all' and success):
            success = test_apa102(client)
        
        return 0 if success else 1
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
