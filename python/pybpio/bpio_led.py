"""
BPIO LED Implementation for Bus Pirate 5

This file implements the LED protocol interface for the Bus Pirate BPIO2 
flatbuffer protocol. It supports WS2812, APA102, and onboard RGB LEDs.

Usage:
    from pybpio.bpio_client import BPIOClient
    from pybpio.bpio_led import BPIOLED
    
    # Connect to Bus Pirate
    client = BPIOClient('COM3')
    
    # Initialize LED interface
    led = BPIOLED(client)
    
    # Configure for WS2812 external LEDs
    led.configure(led_type='WS2812')
    
    # Set LED colors
    led.set_rgb(255, 0, 0)  # Red
    
    # Or use onboard RGB
    led.configure(led_type='ONBOARD')
    led.set_rgb(0, 255, 0)  # Green
    
    client.close()
"""

from .bpio_base import BPIOBase

class BPIOLED(BPIOBase):
    # LED type constants
    LED_WS2812 = 0
    LED_APA102 = 1
    LED_ONBOARD = 2
    
    def __init__(self, client):
        super().__init__(client)
        self.led_type = None
        
    def configure(self, led_type='WS2812', **kwargs):
        """Configure LED mode
        
        Args:
            led_type (str or int): LED type - 'WS2812', 'APA102', or 'ONBOARD' (or 0, 1, 2)
            **kwargs: Additional configuration parameters
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        kwargs['mode'] = 'LED'
        
        # Convert string to submode number
        if isinstance(led_type, str):
            led_type_upper = led_type.upper()
            if led_type_upper == 'WS2812':
                submode = self.LED_WS2812
            elif led_type_upper == 'APA102':
                submode = self.LED_APA102
            elif led_type_upper == 'ONBOARD':
                submode = self.LED_ONBOARD
            else:
                print(f"Invalid LED type: {led_type}. Use 'WS2812', 'APA102', or 'ONBOARD'")
                return False
        else:
            submode = led_type
            
        # Validate submode
        if submode not in [0, 1, 2]:
            print(f"Invalid LED submode: {submode}. Use 0 (WS2812), 1 (APA102), or 2 (ONBOARD)")
            return False
        
        self.led_type = submode
        
        # Get the existing mode_configuration from kwargs or create a new one
        mode_configuration = kwargs.get('mode_configuration', {})
        mode_configuration['submode'] = submode
        kwargs['mode_configuration'] = mode_configuration

        success = self.client.configuration_request(**kwargs)         
        self.configured = success
        return success
    
    def write(self, data):
        """Write raw data to LED device
        
        Args:
            data (bytes or list): Raw data to write to LEDs
            
        Returns:
            dict: Response from device, None if error
        """
        if not self.config_check():
            return None
            
        return self.client.data_request(
            start_main=True,
            data_write=data,
            stop_main=True
        )
    
    def set_rgb(self, r, g, b, brightness=31):
        """Set a single LED to RGB color
        
        For ONBOARD: Sets the onboard RGB LED (brightness ignored)
        For WS2812: Sets first LED in the chain (brightness ignored)
        For APA102: Sets first LED with brightness control
        
        Args:
            r (int): Red value 0-255
            g (int): Green value 0-255
            b (int): Blue value 0-255
            brightness (int): Brightness 0-31 for APA102 (default: 31 = max, ignored for others)
            
        Returns:
            dict: Response from device, None if error
        """
        if not self.config_check():
            return None
        
        # WS2812 and onboard use GRB order, APA102 uses RGB with brightness
        # Reset (WS2812/onboard)/START FRAME (APA102) is handled by 
        # setting the start_main and stop_main flags in the write() method
        if self.led_type == self.LED_WS2812: 
            # WS2812 format: GRB (brightness ignored)
            data = bytes([g, r, b])
        elif self.led_type == self.LED_ONBOARD:
            # Onboard RGB format: RGB (brightness ignored)
            data = bytes([r, g, b])
        elif self.led_type == self.LED_APA102:
            # APA102 format: BRG with brightness byte
            # Brightness: 3 MSB = 111, 5 LSB = brightness (0-31)
            brightness_byte = 0xE0 | (brightness & 0x1F)
            data = bytes([brightness_byte, b, g, r])
        else:
            print("LED type not configured")
            return None
            
        return self.write(data)
 
    def set_rgbw(self, r, g, b, w, brightness=31):
        """Set a single RGBW LED (WS2812 only)
        
        Args:
            r (int): Red value 0-255
            g (int): Green value 0-255
            b (int): Blue value 0-255
            w (int): White value 0-255
            brightness (int): Brightness 0-31 (ignored for WS2812, kept for API consistency)
            
        Returns:
            dict: Response from device, None if error
        """
        if not self.config_check():
            return None
            
        if self.led_type != self.LED_WS2812:
            print("RGBW only supported for WS2812 LEDs")
            return None
        
        # WS2812 RGBW format: GRBW (brightness ignored)
        data = bytes([g, r, b, w])
        return self.write(data)

    def set_multiple_rgb(self, colors, brightness=31):
        """Set multiple LEDs with RGB values
        
        Args:
            colors (list of tuples): List of (r, g, b) tuples, one per LED
            brightness (int): Brightness 0-31 for APA102 (default: 31 = max, ignored for others)
            
        Returns:
            dict: Response from device, None if error
        """
        if not self.config_check():
            return None
        
        if self.led_type == self.LED_WS2812 or self.led_type == self.LED_ONBOARD:
            # WS2812 format: GRB per LED (brightness ignored)
            data = bytearray()
            for r, g, b in colors:
                data.extend([g, r, b])
        elif self.led_type == self.LED_APA102:
            # APA102 format: LED frames with brightness
            # Brightness: 3 MSB = 111, 5 LSB = brightness (0-31)
            brightness_byte = 0xE0 | (brightness & 0x1F)
            data = bytearray()
            for r, g, b in colors:
                data.extend([brightness_byte, b, g, r])
        else:
            print("LED type not configured")
            return None
            
        return self.write(data)
    
    def clear(self, num_leds=1):
        """Turn off LEDs (set to black)
        
        Args:
            num_leds (int): Number of LEDs to clear (default: 1)
            
        Returns:
            dict: Response from device, None if error
        """
        colors = [(0, 0, 0)] * num_leds
        return self.set_multiple_rgb(colors)
