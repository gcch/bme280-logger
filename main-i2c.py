import datetime
import socket
import configparser
import board
from adafruit_bme280 import basic as adafruit_bme280
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# config
config = configparser.ConfigParser()
CONFIG_FILE = "config.ini"
config.read(CONFIG_FILE, encoding="utf8")

def main():

    device_name = config.get("Device", "name", fallback="bme280")
    device_i2c_address = config.get("Device", "address", fallback=0x76)
    hostname = socket.gethostname()

    # Get data
    i2c = board.I2C()
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    bme280.sea_level_pressure = 1013.25
    timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    df = {
        '_time': timestamp,
        'measurement': 'env-sensor',
        'tags': { 
            'client': hostname,
            'sensor': device_name
        },
        'fields': {
            'temperature': bme280.temperature,
            'pressure': bme280.pressure,
            'humidity': bme280.humidity
        }
    }
    #print(df)
    
    # Write to InfluxDB
    url = config.get("InfluxDB", "url", fallback="")
    org = config.get("InfluxDB", "org", fallback="")
    token = config.get("InfluxDB", "token", fallback="")
    bucket = config.get("InfluxDB", "Bucket", fallback="")
    client = influxdb_client.InfluxDBClient(url, token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=df)

if __name__ == "__main__":
    main()
