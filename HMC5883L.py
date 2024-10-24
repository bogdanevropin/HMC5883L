#!/usr/bin/env python
# vim: set fileencoding=UTF-8 :

# HMC5888L Magnetometer (Digital Compass) wrapper class
# Based on https://bitbucket.org/thinkbowl/i2clibraries/src/14683feb0f96,
# but uses smbus rather than quick2wire and sets some different init
# params.

import smbus
import math
from time import sleep
import sys


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

    def __init__(self, port=1, address=0x0D, gauss=1.3, declination=(0, 0)):
        self.bus = smbus.SMBus(port)
        self.address = address
        r = int(input('reg?\n'))
        self.reg = r

        (degrees, minutes) = declination
        self.__declDegrees = degrees
        self.__declMinutes = minutes
        self.__declination = (degrees + minutes / 60) * math.pi / 180
        print('Start init HMC4883L')

        (reg, self.__scale) = self.__scales[gauss]
        self.bus.write_byte_data(self.address, 0x00, 0x70)  # 8 Average, 15 Hz, normal measurement
        print('8 Average, 15 Hz, normal measurement')
        sleep(0.1)
        self.bus.write_byte_data(self.address, 0x01, reg << 5)  # Scale
        print('Scale')
        sleep(0.1)
        self.bus.write_byte_data(self.address, 0x02, 0x00)  # Continuous measurement
        print('Continous measurment')
        sleep(0.1)

    def declination(self):
        return self.__declDegrees, self.__declMinutes

    @staticmethod
    def twos_complement(val, length):
        # Convert twos compliment to integer
        if val & (1 << length - 1):
            val = val - (1 << length)
        return val

    def __convert(self, data, offset):
        val = self.twos_complement((data[offset] << 8) | data[offset + 1], 16)
        if val == -4096:
            return None
        return round(val * self.__scale, 4)

    def axes(self):
        # Read data from registers 03 to 08 (Data Output X, Y, Z MSB and LSB)
        data = self.bus.read_i2c_block_data(self.address, 0x00, 6)
        print(data)
        # Combine MSB and LSB values to get the complete 16-bit values
        x = self.__convert(data, 3)
        y = self.__convert(data, 7)
        z = self.__convert(data, 5)
        return x, y, z

    def heading(self):
        x, y, z = self.axes()
        heading_rad = math.atan2(y, x)
        heading_rad += self.__declination

        # Correct for reversed heading
        if heading_rad < 0:
            heading_rad += 2 * math.pi

        # Check for wrap and compensate
        elif heading_rad > 2 * math.pi:
            heading_rad -= 2 * math.pi

        # Convert to degrees from radians
        heading_deg = heading_rad * 180 / math.pi
        return heading_deg

    @staticmethod
    def degrees(heading_deg):
        degrees = math.floor(heading_deg)
        minutes = round((heading_deg - degrees) * 60)
        return degrees, minutes

    def __str__(self):
        x, y, z = self.axes()
        return "Axis X: " + str(x) + "\n" \
               "Axis Y: " + str(y) + "\n" \
               "Axis Z: " + str(z) + "\n" \
               "Declination: " + str(self.degrees(self.__declination)) + "\n" \
               "Heading: " + str(self.degrees(self.heading())) + "\n"


if __name__ == "__main__":
    print('Start')
    try:
        # http://magnetic-declination.com/Great%20Britain%20(UK)/Harrogate# -2,5
        compass = HMC5883L(gauss=4.7, declination=(8, 29))
        run = True
        while run:
            heading = str(compass.degrees(compass.heading()))
            sys.stdout.write("\rHeading: " + heading + "\n")
            a = input('next?')
            if a == 'e':
                run = False
    # except Exception as e:
    #     print(e)

    except KeyboardInterrupt:
        print("Measurement stopped by user")
