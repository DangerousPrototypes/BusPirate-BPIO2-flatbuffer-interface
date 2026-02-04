"""
BPIO UART Implementation for Bus Pirate 5

This file implements the UART protocol interface for the Bus Pirate BPIO2 
flatbuffer protocol. It provides both synchronous transactions and 
asynchronous data monitoring capabilities.

Usage:
    from pybpio.bpio_client import BPIOClient
    from pybpio.bpio_uart import BPIOUART
    
    # Connect to Bus Pirate
    client = BPIOClient('COM3')
    
    # Initialize UART interface
    uart = BPIOUART(client)
    uart.configure(speed=115200, parity=False, data_bits=8, stop_bits=1)
    
    # Send data
    uart.write(b"Hello World!\r\n")
    
    # Receive data
    response = uart.read(10)
    
    # Monitor for asynchronous data
    async_data = uart.get_async_data()
    
    client.close()
"""

from .bpio_base import BPIOBase
import threading
import time

class BPIOUART(BPIOBase):
    def __init__(self, client):
        super().__init__(client)
        self._async_buffer = []
        self._async_lock = threading.Lock()
        self._monitoring = False
        
    def configure(self, speed=115200, data_bits=8, parity=False, stop_bits=1, 
                  flow_control=False, signal_inversion=False, **kwargs):
        """Configure UART mode
        
        Args:
            speed (int): Baud rate in bps (default: 115200)
            data_bits (int): Number of data bits, 5-8 (default: 8)
            parity (bool): Enable even parity (default: False = no parity)
            stop_bits (int): Number of stop bits, 1 or 2 (default: 1)
            flow_control (bool): Enable hardware flow control (default: False)
            signal_inversion (bool): Invert UART signals (default: False)
            **kwargs: Additional configuration parameters
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        kwargs['mode'] = 'UART'
        
        # Get the existing mode_configuration from kwargs or create a new one
        mode_configuration = kwargs.get('mode_configuration', {})
        
        # Set the UART configuration parameters
        mode_configuration['speed'] = speed
        mode_configuration['data_bits'] = data_bits
        mode_configuration['parity'] = parity
        mode_configuration['stop_bits'] = stop_bits
        mode_configuration['flow_control'] = flow_control
        mode_configuration['signal_inversion'] = signal_inversion
        
        # Replace the mode_configuration in kwargs
        kwargs['mode_configuration'] = mode_configuration

        success = self.client.configuration_request(**kwargs)         
        self.configured = success
        return success
    
    def write(self, data):
        """Write data to UART
        
        Args:
            data (bytes or list): Data to transmit
            
        Returns:
            dict: Response from device, None if error
        """
        if not self.config_check():
            return None
            
        return self.client.data_request(data_write=data)
    
    def read(self, num_bytes):
        """Read bytes from UART
        
        Args:
            num_bytes (int): Number of bytes to read
            
        Returns:
            dict: Response containing read data, None if error
        """
        if not self.config_check():
            return None
            
        return self.client.data_request(bytes_read=num_bytes)
        
    def transfer(self, write_data, read_bytes=None):
        """Perform UART write followed by read
        
        Args:
            write_data (bytes or list): Data to write
            read_bytes (int): Number of bytes to read (optional)
            
        Returns:
            dict: Response containing read data if requested, None if error
        """
        if not self.configured:
            print("UART not configured. Call configure() first.")
            return None
            
        return self.client.data_request(
            data_write=write_data,
            bytes_read=read_bytes
        )
    
    def start_async_monitoring(self, callback=None):
        """Start monitoring for asynchronous UART data
        
        Args:
            callback (function): Optional callback function called when async data arrives
                                 Function signature: callback(data_bytes)
        """
        if not self.configured:
            print("UART not configured. Call configure() first.")
            return False
            
        self._monitoring = True
        self._async_callback = callback
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._async_monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        return True
    
    def stop_async_monitoring(self):
        """Stop monitoring for asynchronous UART data"""
        self._monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1.0)
    
    def get_async_data(self):
        """Get any accumulated asynchronous data
        
        Returns:
            list: List of byte arrays received asynchronously
        """
        with self._async_lock:
            data = self._async_buffer[:]
            self._async_buffer.clear()
            return data
    
    def _async_monitor_loop(self):
        """Internal monitoring loop for async data"""
        while self._monitoring and self.configured:
            try:
                # Check for async data using a very short timeout
                async_data = self.client.check_async_data(timeout=0.1)
                
                if async_data and async_data.get('is_async', False):
                    data_read = async_data.get('data_read', [])
                    
                    if data_read:
                        with self._async_lock:
                            self._async_buffer.append(bytes(data_read))
                        
                        # Call callback if provided
                        if hasattr(self, '_async_callback') and self._async_callback:
                            try:
                                self._async_callback(bytes(data_read))
                            except Exception as e:
                                print(f"Async callback error: {e}")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Async monitoring error: {e}")
                break
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, '_monitoring') and self._monitoring:
            self.stop_async_monitoring()
