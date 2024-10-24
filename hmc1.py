import smbus
import time

class HMC5883L:
    def __init__(self, bus=1, address=0x1a):
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.init_config()

    def init_config(self):
        self.bus.write_byte_data(self.address, 0x0B, 0x01)
        time.sleep(0.1)  # Adjust the delay as needed
        self.bus.write_byte_data(self.address, 0x20, 0x40)
        time.sleep(0.1)  # Adjust the delay as needed
        self.bus.write_byte_data(self.address, 0x21, 0x01)
        time.sleep(0.1)  # Adjust the delay as needed
        self.bus.write_byte_data(self.address, 0x09, 0x0d)  # Adjust this value for your required configuration
        time.sleep(0.1)  # Adjust the delay as needed

    def read_axes(self):
        data = self.bus.read_i2c_block_data(self.address, 0x00, 6)
        x = self.convert_data(data[0], data[1])
        y = self.convert_data(data[2], data[3])
        z = self.convert_data(data[4], data[5])
        return x, y, z

    def convert_data(self, low, high):
        value = (high << 8) + low
        # Convert to signed value if necessary
        if value & (1 << 15):
            value -= 1 << 16
        return value

    def is_data_ready(self):
        status = self.bus.read_byte_data(self.address, 0x06)
        return (status & 0x01) != 0

if __name__ == "__main__":
    sensor = HMC5883L()

    try:
        while True:
            if sensor.is_data_ready():
                x, y, z = sensor.read_axes()
                print("X: {}, Y: {}, Z: {}".format(x, y, z))
            time.sleep(0.1)  # Adjust the delay as needed
    except KeyboardInterrupt:
        print("Measurement stopped by user")
