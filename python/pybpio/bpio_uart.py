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
                  flow_control=False, signal_inversion=False, async_callback=None, **kwargs):
        """Configure UART mode
        
        Args:
            speed (int): Baud rate in bps (default: 115200)
            data_bits (int): Number of data bits, 5-8 (default: 8)
            parity (bool): Enable even parity (default: False = no parity)
            stop_bits (int): Number of stop bits, 1 or 2 (default: 1)
            flow_control (bool): Enable hardware flow control (default: False)
            signal_inversion (bool): Invert UART signals (default: False)
            async_callback (function): Optional callback for async data: callback(data_bytes)
                                      If provided, async data goes to callback instead of buffer
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
        
        # If monitoring is already running, stop it first to reconfigure
        if self._monitoring:
            self._stop_async_monitoring()
            # Small delay to ensure thread has fully stopped
            time.sleep(0.1)
        
        # Clear any pending async data in the client's queue
        self.client.clear_async_queue()
        
        # Store callback if provided
        self._async_callback = async_callback
        
        # Clear any buffered data when reconfiguring
        with self._async_lock:
            self._async_buffer.clear()
        
        # Automatically start async monitoring when UART is configured
        if success:
            self._start_async_monitoring()
            # Small delay to ensure monitoring thread is ready
            time.sleep(0.05)
        
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
    
    def read_async(self, clear_buffer=True):
        """Read any accumulated asynchronous data from the buffer.
        
        This method retrieves data that was received asynchronously from the 
        UART interface. Async monitoring starts automatically when configure() 
        is called, so you can simply call read_async() at any time to get data.
        
        Note: If an async_callback was provided to configure(), data goes directly
        to the callback and is not buffered. This method only returns buffered data.
        
        Args:
            clear_buffer (bool): If True, clear the buffer after reading (default: True)
                                If False, keep data in buffer for next read
        
        Returns:
            bytes: Concatenated async data received, or empty bytes if none available
        """
        with self._async_lock:
            if not self._async_buffer:
                return b''
            
            # Concatenate all buffered chunks into single bytes object
            result = b''.join(self._async_buffer)
            
            if clear_buffer:
                self._async_buffer.clear()
            
            return result
    
    def _start_async_monitoring(self):
        """Internal: Start monitoring for asynchronous UART data"""
        if self._monitoring:
            return
            
        self._monitoring = True
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._async_monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def _stop_async_monitoring(self):
        """Internal: Stop monitoring for asynchronous UART data"""
        self._monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1.0)
    
    def _async_monitor_loop(self):
        """Internal monitoring loop for async data"""
        while self._monitoring and self.configured:
            try:
                # Check for async data using a very short timeout
                async_data = self.client.check_async_data(timeout=0.1)
                
                if async_data and async_data.get('is_async', False):
                    data_read = async_data.get('data_read', [])
                    
                    if data_read:
                        data_bytes = bytes(data_read)
                        
                        # If callback is provided, call it; otherwise buffer the data
                        if hasattr(self, '_async_callback') and self._async_callback:
                            try:
                                self._async_callback(data_bytes)
                            except Exception as e:
                                print(f"Async callback error: {e}")
                        else:
                            # No callback - accumulate in buffer for read_async()
                            with self._async_lock:
                                self._async_buffer.append(data_bytes)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Async monitoring error: {e}")
                break
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, '_monitoring') and self._monitoring:
            self._stop_async_monitoring()
