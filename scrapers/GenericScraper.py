import json
import logging
from datetime import datetime

import requests

from scrapers.utils.timestamp import TimestampUtils

logging.basicConfig(level=logging.INFO)

SENSOR_DATA_URL = "https://allertameteo.regione.emilia-romagna.it/o/api/allerta/get-sensor-values-no-time"

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
    sensor_ids["RAIN"]: "rain",
    sensor_ids["IDRO_LEVEL"]: "idro_level",
    sensor_ids["TEMP"]: "temp",
    sensor_ids["WIND"]: "wind",
    sensor_ids["HUMIDITY"]: "humidity",
}

sensors_units = {
    sensor_ids["RAIN"]: "mm",
    sensor_ids["IDRO_LEVEL"]: "m",
    sensor_ids["TEMP"]: "K",
    sensor_ids["WIND"]: "m/s",
    sensor_ids["HUMIDITY"]: "%",
}


class GenericDetection:
    def __init__(self):
        self.sensorId: str | None = None
        self.sensorName: str | None = None
        self.sensorType: str | None = None
        self.unit: str | None = None
        self.timestamp: int | None = None
        self.longitude: int | None = None
        self.latitude: int | None = None
        self.value: int | None = None
        self.queries: list[tuple[str, int]] = []

    def to_json(self) -> dict:
        query: tuple[str, int] | None = self.__is_alert()

        if query is not None:
            return {
                "isAlert": True,
                "detection": {
                    "sensorName": self.sensorName,
                    "type": self.sensorType,
                    "value": self.value,
                    "unit": self.unit,
                    "timestamp": self.timestamp,
                    "query": {
                        "name": query[0],
                        "value": query[1],
                    },
                },
            }

        return {
            "isAlert": False,
            "detection": {
                "sensorId": self.sensorId,
                "sensorName": self.sensorName,
                "unit": self.unit,
                "timestamp": self.timestamp,
                "longitude": self.longitude,
                "latitude": self.latitude,
                "value": self.value,
            },
        }

    def to_json_detection(self) -> dict:
        return {
            "sensorId": self.sensorId,
            "sensorName": self.sensorName,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "value": self.value,
        }

    def __is_alert(self) -> tuple[str, int] | None:
        if self.value is None:
            return None

        query: tuple[str, int] | None = None
        for threshold in sorted(self.queries, key=lambda x: x[0]):
            if self.value >= threshold[1]:
                query = threshold

        return query


class GenericScraper:
    def __init__(self, sensor_name: str):
        self.logger = logging.getLogger(str(self.__class__))

        if sensor_name.upper() not in sensor_ids:
            raise KeyError(f"Unrecognized sensor '{sensor_name}'")

        self.selected_sensor_name = sensor_name.upper()
        self.selected_sensor_id: str = sensor_ids[self.selected_sensor_name]

    def scrape(self, dump: bool = False) -> dict:
        now = TimestampUtils().get_compliant_now_timestamp()
        res = requests.get(
            SENSOR_DATA_URL,
            params={
                "variabile": self.selected_sensor_id,
                "time": now,
            },
        ).json()

        self.logger.info(
            f"Retrieved data for sensor {self.selected_sensor_name} for date: {datetime.fromtimestamp(now/ 1000)}"
        )

        data = {
            "timestamp": res[0]["time"],
            "sensor_type": sensors_names[self.selected_sensor_id],
            "unit": sensors_units[self.selected_sensor_id],
            "data": res[1:],
        }

        if dump:
            with open(
                f"{sensors_names[self.selected_sensor_id]}_{now}_data.json", "w"
            ) as w:
                json.dump(data, w, indent=2)

        return data

    def detections_from_scraped_data(self, data: dict) -> list[GenericDetection]:
        res = []
        for detection in data["data"]:
            d = GenericDetection()
            d.sensorId = detection["idstazione"]
            d.sensorName = detection["nomestaz"]
            d.sensorType = data["sensor_type"]
            d.unit = data["unit"]
            d.timestamp = data["timestamp"]
            d.longitude = detection["lon"]
            d.latitude = detection["lat"]
            d.value = detection["value"]
            for name in ["soglia1", "soglia2", "soglia3"]:
                if name in detection:
                    d.queries.append((name, detection[name]))
            res.append(d)
        return res

    def get_detection_for_sensor(self, sensor_name: str) -> GenericDetection | None:
        detections = self.detections_from_scraped_data(self.scrape(dump=False))
        filtered = filter(lambda x: x.sensorName == sensor_name, detections)
        return next(filtered, None)


if __name__ == "__main__":
    for name in sensors:
        GenericScraper(name).scrape(dump=True)
