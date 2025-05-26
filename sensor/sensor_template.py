from scrapers.GenericScraper import GenericScraper, GenericDetection
import requests
import signal
import sys
import re
import os
import signal
import time
import datetime
from fastapi import FastAPI, Response, status, Request
from collections import defaultdict
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


cronjob_days_pattern = r"^([0-6])-([0-6])$"

# Sensor configuration
name = "{{ SENSOR_INFORMATION_NAME }}"
type = "{{ SENSOR_INFORMATION_TYPE }}"
description = "{{ SENSOR_INFORMATION_DESCRIPTION }}"
queries = {{SENSOR_INFORMATION_QUERIES}}

ip = "{{  SENSOR_ETHERNET_IP }}"
port = {{SENSOR_ETHERNET_PORT}}

registry = "{{ SENSOR_REGISTRY_URL }}"
apikey = "{{ SENSOR_REGISTRY_KEY }}"
registerPath = "{{ SENSOR_REGISTRY_REGISTERPATH }}"
shutdownPath = "{{ SENSOR_REGISTRY_SHUTDOWNPATH }}"

# API Gateway information
api_gatewat_info = {
    "url": "{{ SENSOR_APIGATEWAY_URL }}",
    "port": {{SENSOR_APIGATEWAY_PORT}},
}
# Cron task configuration
cron_info = {
    "day_of_the_week": "{{ SENSOR_CRONJOB_DAY_OF_WEEK }}",
    "hour": "{{ SENSOR_CRONJOB_HOUR }}",
    "minute": "{{ SENSOR_CRONJOB_MINUTE }}",
}
MONDAY, SUNDAY = 0, 6
MIN_HOUR, MAX_HOUR, MIN_MINUTE, MAX_MINUTE = 0, 23, 0, 59
MAX_PORT = 65_535

scraper = GenericScraper(type)

app = FastAPI()
scheduler = BackgroundScheduler()


@app.on_event("shutdown")
def shutdown_handler():
    log("Graceful shutdown triggered...")
    requests.delete(
        url=registry + shutdownPath,
        params={"sensorIp": ip, "sensorPort": port},
        headers={"x-api-key": apikey},
    )
    sys.exit(0)


def log(message: str):
    print(f"[{datetime.datetime.now()}]: {message}.")


def clear_data(input_json_data: dict):
    return input_json_data


def register_sensor() -> None:
    log("Register the Sensor")
    attempts = 10
    time_to_wait = 5
    for _ in range(attempts):
        try:
            response: Response = requests.post(
                url=registry + registerPath,
                headers={"x-api-key": apikey},
                json={
                    "sensorIp": ip,
                    "sensorName": name,
                    "sensorPort": port,
                    "sensorType": type,
                    "sensorQueries": queries,
                },
            )
            log(response)
            response.raise_for_status()
            if response.status_code == status.HTTP_201_CREATED:
                log("Registered.")
                return
            time.sleep(time_to_wait)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        ) as error:
            log(f"Error: {repr(error)}, retrying in 5 seconds")
            time.sleep(time_to_wait)
    log("Failed to connect. exiting...")
    sys.exit(1)


def sense_data() -> GenericDetection | None:
    log("Sensing the data")
    return scraper.get_detection_for_sensor(name)


def send_data_to_endpoint():
    try:
        log("Prepare to send the send the data to the API gateway")
        raw_data = sense_data()
        if raw_data is None:
            log("Cannot retrieve data, scraper scraped nothing!")
            return

        data = raw_data.to_json()
        url = f"https://{api_gatewat_info['url']}/v0/api/detection"

        if data["isAlert"] and bool(data["isAlert"]):
            requests.post(url=url + "/alerts", json=data["detection"])
            log("Alert sent to the API gateway")

        data = raw_data.to_json_detection()
        url = f"{url}/{type}/{data['sensorName']}/detections"
        requests.post(url=url, json=data)

        log("Data sent to the API gateway")
    except (ValueError, requests.exceptions.JSONDecodeError) as error:
        log(f"An error occurred -> {repr(error)}")


def config_scheduler() -> None:
    global scheduler
    log(
        f"Configuring the scheduler with the following infomrations: Day: {
            cron_info['day_of_the_week']}, Hour: {cron_info['hour']}, Minute: {cron_info['minute']}"
    )
    if scheduler.running:
        scheduler.shutdown()
        scheduler = BackgroundScheduler()

    scheduler.add_job(
        send_data_to_endpoint,
        "cron",
        day_of_week=cron_info["day_of_the_week"],
        hour=cron_info["hour"],
        minute=cron_info["minute"],
        timezone="UTC",
    )
    log(f"New Cron task configured")
    scheduler.start()


@app.put("/sensor/update/name")
async def update_sensor_name(request: Request, response: Response) -> Response:
    log("Received a request to update the Sensor's name")
    new_name: str = (await request.json())["sensorName"]
    print(new_name)
    if new_name and len(new_name.replace(" ", "")) > 0:
        global name
        name = new_name.replace(" ", "")
        return Response()
    else:
        return Response(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content="Error: The input name can not be None",
        )


@app.put("/sensor/configuration/cron/days")
async def update_sensor_date(request: Request, response: Response) -> Response:
    days: str = (await request.json())["sensorCronJobDays"]
    match = re.match(cronjob_days_pattern, days)
    if match and int(match.group(1) <= match.group(2)):
        log("Received a request to update the Sensor's days of work with: " + days)
        cron_info["day_of_the_week"] = f"{days}"
        config_scheduler()
        return Response()
    else:
        return Response(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content="Error: The input days must be in [0, 6]",
        )


@app.put("/sensor/configuration/cron/time")
async def update_sensor_time(request: Request, response: Response) -> Response:
    data = await request.json()
    hour: int = int(data["sensorCronJobTimeHour"])
    minute: int = int(data["sensorCronJobTimeMinute"])
    log(data)
    if MIN_HOUR <= hour <= MAX_HOUR and MIN_MINUTE <= minute <= MAX_MINUTE:
        log("Received a new request to update the Sensor's time of work")
        cron_info["hour"] = f"{hour}"
        cron_info["minute"] = f"{minute}"
        config_scheduler()
        response = Response()
    else:
        response = Response(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content="Error: The input hours must be in [0, 23] and minutes in [0, 59]",
        )
    return response


@app.put("/sensor/configuration/gateway/url")
def update_sensor_gateway_url(
    response: Response, new_url: str = api_gatewat_info["url"]
) -> Response:
    if len(new_url) > 0 and len(new_url.replace(" ", "")) > 0:
        log("Received a new request to update the Sensor's gateway url")
        api_gatewat_info["url"] = new_url
        return Response()
    else:
        return Response(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content="Error: the gateway url should be non empty and should not contains only withe spaces",
        )


@app.put("/sensor/configuration/gateway/port")
def update_sensor_gateway_url(
    response: Response, port: int = api_gatewat_info["port"]
) -> Response:
    if 0 <= port <= MAX_PORT:
        log("Received a new request to update the Sensor's gateway url")
        api_gatewat_info["port"] = port
        return Response()
    else:
        return Response(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content="Error: the gateway url should be non empty and should not contains only withe spaces",
        )


@app.get("/health")
def health(response: Response) -> Response:
    log("Server pinged")
    return Response(content="Everything is OK.")


@app.get("/info")
def info(response: Response) -> Response:
    log("Returning Sensor information")
    key = "General Sensor Information"
    message: dict[str, list] = defaultdict(list)
    message[key].append({"Sensor Name": name})
    message[key].append({"Description": description})
    message[key].append({"Endpoint Information": api_gatewat_info})
    message[key].append({"Cronjob Information": cron_info})

    response: Response = Response(content=json.dumps(message))
    response.headers["Content-Type"] = "application/json"
    return response


@app.delete("/shutdown")
def shutoff(response: Response) -> Response:
    log("Shutting down the sensor")
    try:
        log("Return OK to the client")
        return Response(status_code=200, content="Server shutting down...")
    finally:
        log("exiting...")
        os.kill(os.getpid(), signal.SIGTERM)


if __name__ == "__main__":
    config_scheduler()
    register_sensor()
    # signal.signal(signal.SIGINT, shutdown_handler)
    # register the sensor to the MAIN system
    # start the sensor server

    uvicorn.run(app, host=ip, port=port)
