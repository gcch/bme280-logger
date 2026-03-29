import datetime
import socket
import configparser
import smbus2
import struct
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# config
config = configparser.ConfigParser()
CONFIG_FILE = "config.ini"
config.read(CONFIG_FILE, encoding="utf8")


class BME280:
    """smbus2ベースの最小BME280ドライバ"""

    def __init__(self, bus: smbus2.SMBus, address: int = 0x76):
        self.bus = bus
        self.address = address
        self._load_calibration()
        # forced mode / osrs_t=1 / osrs_p=1 / osrs_h=1
        self.bus.write_byte_data(self.address, 0xF2, 0x01)
        self.bus.write_byte_data(self.address, 0xF4, 0x25)

    def _load_calibration(self):
        raw = self.bus.read_i2c_block_data(self.address, 0x88, 24)
        self.dig_T1 = struct.unpack_from('<H', bytes(raw), 0)[0]
        self.dig_T2 = struct.unpack_from('<h', bytes(raw), 2)[0]
        self.dig_T3 = struct.unpack_from('<h', bytes(raw), 4)[0]
        self.dig_P1 = struct.unpack_from('<H', bytes(raw), 6)[0]
        self.dig_P2 = struct.unpack_from('<h', bytes(raw), 8)[0]
        self.dig_P3 = struct.unpack_from('<h', bytes(raw), 10)[0]
        self.dig_P4 = struct.unpack_from('<h', bytes(raw), 12)[0]
        self.dig_P5 = struct.unpack_from('<h', bytes(raw), 14)[0]
        self.dig_P6 = struct.unpack_from('<h', bytes(raw), 16)[0]
        self.dig_P7 = struct.unpack_from('<h', bytes(raw), 18)[0]
        self.dig_P8 = struct.unpack_from('<h', bytes(raw), 20)[0]
        self.dig_P9 = struct.unpack_from('<h', bytes(raw), 22)[0]
        self.dig_H1 = self.bus.read_byte_data(self.address, 0xA1)
        raw2 = self.bus.read_i2c_block_data(self.address, 0xE1, 7)
        self.dig_H2 = struct.unpack_from('<h', bytes(raw2), 0)[0]
        self.dig_H3 = raw2[2]
        self.dig_H4 = (raw2[3] << 4) | (raw2[4] & 0x0F)
        self.dig_H5 = (raw2[5] << 4) | (raw2[4] >> 4)
        self.dig_H6 = struct.unpack_from('<b', bytes(raw2), 6)[0]

    def _read_raw(self):
        data = self.bus.read_i2c_block_data(self.address, 0xF7, 8)
        raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_h = (data[6] << 8) | data[7]
        return raw_p, raw_t, raw_h

    def _compensate_temperature(self, raw_t):
        v1 = (raw_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        v2 = (raw_t / 131072.0 - self.dig_T1 / 8192.0) ** 2 * self.dig_T3
        self.t_fine = v1 + v2
        return self.t_fine / 5120.0

    def _compensate_pressure(self, raw_p):
        v1 = self.t_fine / 2.0 - 64000.0
        v2 = v1 * v1 * self.dig_P6 / 32768.0
        v2 += v1 * self.dig_P5 * 2.0
        v2 = v2 / 4.0 + self.dig_P4 * 65536.0
        v1 = (self.dig_P3 * v1 * v1 / 524288.0 + self.dig_P2 * v1) / 524288.0
        v1 = (1.0 + v1 / 32768.0) * self.dig_P1
        if v1 == 0:
            return 0.0
        p = 1048576.0 - raw_p
        p = (p - v2 / 4096.0) * 6250.0 / v1
        v1 = self.dig_P9 * p * p / 2147483648.0
        v2 = p * self.dig_P8 / 32768.0
        return (p + (v1 + v2 + self.dig_P7) / 16.0) / 100.0  # hPa

    def _compensate_humidity(self, raw_h):
        h = self.t_fine - 76800.0
        if h == 0:
            return 0.0
        h = (raw_h - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) * (
            self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h * (
                1.0 + self.dig_H3 / 67108864.0 * h)))
        h *= 1.0 - self.dig_H1 * h / 524288.0
        return max(0.0, min(100.0, h))

    def read(self) -> dict:
        raw_p, raw_t, raw_h = self._read_raw()
        temperature = self._compensate_temperature(raw_t)
        return {
            'temperature': round(temperature, 2),
            'pressure':    round(self._compensate_pressure(raw_p), 2),
            'humidity':    round(self._compensate_humidity(raw_h), 2),
        }


def main():
    device_name = config.get("Device", "name", fallback="bme280")
    address_str  = config.get("Device", "address", fallback="0x76")
    i2c_bus      = config.getint("Device", "i2c_bus", fallback=1)
    address      = int(address_str, 0)
    hostname     = socket.gethostname()

    with smbus2.SMBus(i2c_bus) as bus:
        bme280 = BME280(bus, address=address)
        data   = bme280.read()

    timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    df = {
        '_time':       timestamp,
        'measurement': 'env-sensor',
        'tags': {
            'client': hostname,
            'sensor': device_name,
        },
        'fields': data,
    }
    print(df)

    url    = config.get("InfluxDB", "url",    fallback="")
    org    = config.get("InfluxDB", "org",    fallback="")
    token  = config.get("InfluxDB", "token",  fallback="")
    bucket = config.get("InfluxDB", "Bucket", fallback="")

    client    = influxdb_client.InfluxDBClient(url, token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=df)


if __name__ == "__main__":
    main()
