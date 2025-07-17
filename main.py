# XREAL One Pro IMU Retriever Script
# Connects to TCP socket and decodes IMU sensor data
# by Daniel Sami Mitwalli

import socket
import struct
import time
import logging
from dataclasses import dataclass
from typing import Optional, Callable

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
IP = "169.254.2.1"
PORT = 52998
TIMEOUT = 5

# Protocol constants
HEADER = bytes.fromhex("283600000080")
FOOTER = bytes.fromhex("000000cff753e3a59b0000db34b6d782de1b43")
SENSOR_MSG = bytes.fromhex("00401f000040")

# Protocol data offsets
DATA_START_OFFSET = 20  # Could be: timestamp(8) + invariant(2) + static(10)
DATA_END_OFFSET = -26   # Could be: sensor_msg(6) + date_info(20)

@dataclass
class IMUData:
    """IMU sensor data structure"""
    gx: float  # Gyroscope X
    gy: float  # Gyroscope Y
    gz: float  # Gyroscope Z
    ax: float  # Accelerometer X
    ay: float  # Accelerometer Y
    az: float  # Accelerometer Z
    
    def __str__(self):
        return (f"Gx={self.gx:.3f}, Gy={self.gy:.3f}, Gz={self.gz:.3f} | "
                f"Ax={self.ax:.3f}, Ay={self.ay:.3f}, Az={self.az:.3f}")

class IMUReader:
    def __init__(self, ip: str = IP, port: int = PORT, timeout: int = TIMEOUT, 
                 callback: Optional[Callable[[IMUData, int, float], None]] = None):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.message_count = 0
        self.start_time: Optional[float] = None
        self.callback = callback or self.default_callback
        self.logger = logging.getLogger(__name__)
    
    def default_callback(self, imu_data: IMUData, message_count: int, rate: float) -> None:
        """Default callback that prints IMU data"""
        print(f"[{message_count:06d}] {rate:.1f}Hz | {imu_data}")

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def disconnect(self):
        """Close connection and show statistics"""
        if self.sock:
            self.sock.close()
            self.sock = None
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            avg_rate = self.message_count / elapsed if elapsed > 0 else 0
            self.logger.info(f"Processed {self.message_count} messages in {elapsed:.1f}s (avg {avg_rate:.1f}Hz)")

    def decode_imu_data(self, hex_data: str) -> Optional[IMUData]:
        """Extract IMU components from data/hex string"""
        if len(hex_data) < 48:
            return None
            
        chunks = [hex_data[i:i+8] for i in range(0, len(hex_data), 8)]
        if len(chunks) < 6:
            return None
        
        try:
            values = [struct.unpack('<f', bytes.fromhex(chunk))[0] for chunk in chunks[:6]]
            return IMUData(
                ax=values[0], ay=values[1], az=values[2],
                gx=values[5], gy=values[4], gz=values[3]
            )
        except (ValueError, struct.error):
            return None

    def process_message(self, message):
        """Process raw message and extract IMU data"""
        if len(message) < len(HEADER) + 8 + len(FOOTER) + 31:
            return None
            
        # Remove header, session ID (8 bytes), footer, and tail (31 bytes)
        data = message[len(HEADER) + 8:-len(FOOTER) - 31]
        
        if not data.endswith(SENSOR_MSG):
            return None
        
        # Extract IMU data section
        if len(data) < DATA_START_OFFSET + abs(DATA_END_OFFSET):
            return None
            
        data = data[DATA_START_OFFSET:DATA_END_OFFSET]
        return self.decode_imu_data(data.hex())

    def connect(self):
        """Establish TCP connection"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.logger.info(f"Connecting to {self.ip}:{self.port}...")
        self.sock.connect((self.ip, self.port))
        self.logger.info("TCP connected!")
        self.start_time = time.time()

    def run(self):
        """Retrieve and process IMU data"""
        recv_buffer = b""
        
        try:
            if not self.sock:
                self.connect()

            while True:
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        self.logger.info("Connection closed by device.")
                        break

                    recv_buffer += data

                    # Process complete messages
                    while True:
                        header_pos = recv_buffer.find(HEADER)
                        if header_pos == -1:
                            break
                            
                        footer_pos = recv_buffer.find(FOOTER, header_pos)
                        if footer_pos == -1:
                            break

                        # Extract complete message
                        message_end = footer_pos + len(FOOTER)
                        message = recv_buffer[header_pos:message_end]
                        recv_buffer = recv_buffer[message_end:]

                        # Process message and get IMU data
                        imu_data = self.process_message(message)
                        if imu_data:
                            self.message_count += 1
                            elapsed = time.time() - self.start_time
                            rate = self.message_count / elapsed if elapsed > 0 else 0
                            self.callback(imu_data, self.message_count, rate)

                except socket.timeout:
                    self.logger.warning("Socket timeout - retrying...")
                    continue
                except KeyboardInterrupt:
                    self.logger.info("Stopping...")
                    break

        except ConnectionRefusedError:
            self.logger.error(f"Connection refused. Is the device at {self.ip}:{self.port} available?")
        except Exception as e:
            self.logger.error(f"Error: {e}")
        finally:
            self.disconnect()

def main():
    """Main function"""
    with IMUReader() as reader:
        reader.run()

if __name__ == "__main__":
    main()