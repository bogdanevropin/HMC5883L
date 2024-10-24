import math
import smbus
import sys
import time


class HMC5883L:
    __scales = {
        0.88: [0, 0.73],
        1.30: [1, 0.92],
        1.90: [2, 1.22],
        2.50: [3, 1.52],
        4.00: [4, 2.27],
        4.70: [5, 2.56],
        5.60: [6, 3.03],
        8.10: [7, 4.35],
    }

    ConfigurationRegisterA = 0x00
    ConfigurationRegisterB = 0x01
    ModeRegister = 0x02
    AxisXDataRegisterMSB = 0x00
    AxisXDataRegisterLSB = 0x01
    AxisZDataRegisterMSB = 0x02
    AxisZDataRegisterLSB = 0x03
    AxisYDataRegisterMSB = 0x04
    AxisYDataRegisterLSB = 0x05
    StatusRegister = 0x09
    IdentificationRegisterA = 0x10
    IdentificationRegisterB = 0x11
    IdentificationRegisterC = 0x12

    MeasurementContinuous = 0x00
    MeasurementSingleShot = 0x01
    MeasurementIdle = 0x03

    def __init__(self, bus_number=1, address=0x0d, gauss=1.3):
        self.bus = smbus.SMBus(bus_number)
        self.address = address
        self.setScale(gauss)
        self.setDeclination(degree=8.5)
        self.setContinuousMode()

    def __str__(self):
        ret_str = ""
        (x, y, z) = self.getAxes()
        ret_str += "Axis X: " + str(x) + "\n"
        ret_str += "Axis Y: " + str(y) + "\n"
        ret_str += "Axis Z: " + str(z) + "\n"

        ret_str += "Declination: " + self.getDeclinationString() + "\n"

        ret_str += "Heading: " + self.getHeadingString() + "\n"

        return ret_str

    def setContinuousMode(self):
        self.setOption(self.ModeRegister, self.MeasurementContinuous)

    def setScale(self, gauss):
        if gauss not in self.__scales:
            raise ValueError("Invalid gauss value")
        self.scale_reg, self.scale = self.__scales[gauss]
        self.scale_reg = self.scale_reg << 5
        self.setOption(self.ConfigurationRegisterB, self.scale_reg)

    def setDeclination(self, degree, min=0):
        self.declinationDeg = degree
        self.declinationMin = min
        self.declination = (degree + min / 60) * (math.pi / 180)

    def setOption(self, register, value):
        print(f'At adress {self.address} register {register} wrote {value} ')
        self.bus.write_byte_data(self.address, register, value)
        time.sleep(0.1)

    def getDeclination(self):
        return (self.declinationDeg, self.declinationMin)

    def getDeclinationString(self):
        return str(self.declinationDeg) + "\u00b0 " + str(self.declinationMin) + "'"

    def getHeading(self):
        (scaled_x, scaled_y, scaled_z) = self.getAxes()
        print(scaled_x, scaled_y, scaled_z)
        headingRad = math.atan2(scaled_y, scaled_x)
        headingRad += self.declination

        if headingRad < 0:
            headingRad += 2 * math.pi

        if headingRad > 2 * math.pi:
            headingRad -= 2 * math.pi

        headingDeg = headingRad * 180 / math.pi
        degrees = math.floor(headingDeg)
        minutes = round(((headingDeg - degrees) * 60))
        return degrees, minutes

    def getHeadingString(self):
        degrees, minutes = self.getHeading()
        return str(degrees) + "\u00b0 " + str(minutes) + "'"

    def getAxes(self):
        data = self.bus.read_i2c_block_data(self.address, self.AxisXDataRegisterMSB, 6)
        print(data)
        x = self.__convert_to_signed(data[0] << 8 | data[1]) * self.scale
        y = self.__convert_to_signed(data[4] << 8 | data[5]) * self.scale
        z = self.__convert_to_signed(data[2] << 8 | data[3]) * self.scale
        return x, y, z

    @staticmethod
    def __convert_to_signed(val):
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val


if __name__ == "__main__":
    print('Start')
    try:
        compass = HMC5883L(gauss=4.7)
        run = True
        while run:
            heading = compass.getHeadingString()
            sys.stdout.write("\rHeading: " + heading + "\n")
            a = input('next?')
            if a == 'e':
                run = False
    except KeyboardInterrupt:
        print("Measurement stopped by user")
