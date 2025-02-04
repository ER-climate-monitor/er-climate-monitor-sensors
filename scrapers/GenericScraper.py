import json
from utils.timestamp import TimestampUtils
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

SENSOR_DATA_URL="https://allertameteo.regione.emilia-romagna.it/o/api/allerta/get-sensor-values-no-time"

sensors = [
    "RAIN",
    "IDRO_LEVEL",
    "TEMP",
    "WIND",
    "HUMIDITY",
]

sensor_ids = {
    "RAIN": "1,0,3600/1,-,-,-/B13011",
    "IDRO_LEVEL": "254,0,0/1,-,-,-/B13215",
    "TEMP": "254,0,0/103,2000,-,-/B12101",
    "WIND": "254,0,0/103,10000,-,-/B11002",
    "HUMIDITY": "254,0,0/103,2000,-,-/B13003",
}

sensors_names = {
    sensor_ids["RAIN"]: "rain_sensor",
    sensor_ids["IDRO_LEVEL"]: "idro_level_sensor",
    sensor_ids["TEMP"]: "temp_sensor",
    sensor_ids["WIND"]: "wind_sensor",
    sensor_ids["HUMIDITY"]: "humidity_sensor",
}

sensors_units = {
    sensor_ids["RAIN"]: "mm",
    sensor_ids["IDRO_LEVEL"]: "m",
    sensor_ids["TEMP"]: "K",
    sensor_ids["WIND"]: "m/s",
    sensor_ids["HUMIDITY"]: "%",
}

class GenericScraper:
    def __init__(self, sensor_name: str):
        self.logger = logging.getLogger(str(self.__class__))

        if sensor_name not in sensor_ids:
            raise KeyError(f"Unrecognized sensor '{sensor_name}'")

        self.selected_sensor_name = sensor_name
        self.selected_sensor_id: str = sensor_ids[sensor_name]

    def scrape(self, dump: bool = False) -> dict:
        now = TimestampUtils().get_compliant_now_timestamp()
        res = requests.get(SENSOR_DATA_URL, params={
            "variabile": self.selected_sensor_id,
            "time": now,
        }).json()

        self.logger.info(f"Retrieved data for sensor {self.selected_sensor_name} for date: {datetime.fromtimestamp(now/ 1000)}")

        data = {
            "timestamp": res[0]["time"],
            "sensor_type": sensors_names[self.selected_sensor_id],
            "unit": sensors_units[self.selected_sensor_id],
            "data": res[1:],
        }

        if dump:
            with open(f'{sensors_names[self.selected_sensor_id]}_{now}_data.json', 'w') as w:
                json.dump(data, w, indent=2)

        return data
