import board
import busio
import adafruit_bmp280

class BMP280:
    def __init__(self):
        print("[BMP280] Initializing sensor...")
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        self.sensor.sea_level_pressure = 1013.25
        print("[BMP280] configuration complete")

    def read(self):
        print("[BMP280] reading sensor")
        temperature = round(self.sensor.temperature, 2)
        pressure = round(self.sensor.pressure, 2)

        print("[BMP280] temperature = {}".format(temperature))
        print("[BMP280] pressure = {}".format(pressure))

        return {
            'temperature': temperature,
            'pressure': pressure
        }
