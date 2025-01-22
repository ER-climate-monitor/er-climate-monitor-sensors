import requests
import sys
import os
import signal
import time
import datetime
from fastapi import FastAPI, Response, status
from collections import defaultdict
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
import json



# Sensor configuration
name = "{{ SENSOR_INFORMATION_NAME }}"
description = "{{ SENSOR_INFORMATION_DESCRIPTION }}"
ip = "{{  SENSOR_ETHERNET_IP }}"
port = {{ SENSOR_ETHERNET_PORT }}

registry = "{{ SENSOR_REGISTRY_URL }}"
apikey = "{{ SENSOR_REGISTRY_KEY }}"


# API Gateway information
api_gatewat_info = {
    "url": "{{ SENSOR_APIGATEWAY_URL }}",
    "port": {{ SENSOR_APIGATEWAY_PORT }}
}
# Cron task configuration
cron_info = {
    "day_of_the_week": "{{ SENSOR_CRONJOB_DAY_OF_WEEK }}",
    "hour": "{{ SENSOR_CRONJOB_HOUR }}",
    "minute": "{{ SENSOR_CRONJOB_MINUTE }}"
}
MONDAY, SUNDAY = 0, 6
MIN_HOUR, MAX_HOUR, MIN_MINUTE, MAX_MINUTE = 0, 23, 0, 59
MAX_PORT = 65_535

data_endpoint_url = "{{ SENSOR_ENDPOINT_URL }}"

app = FastAPI()
scheduler = BackgroundScheduler()

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
            response: Response = requests.post(url=registry, headers={'apiKey': apikey}, json={
                "sensorIp": ip,
                "sensorName": name,
                "sensorPort": port,
            })
            log(response)
            response.raise_for_status()
            if response.status_code == status.HTTP_201_CREATED:
                log("Registered.")
                return 
            time.sleep(time_to_wait)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError)  as error:
            log(f"Error: {repr(error)}, retrying in 5 seconds")
            time.sleep(time_to_wait)
    log("Failed to connect. exiting...")
    sys.exit(1)
            
        

def sense_data():
    log("Sensing the data")
    response: Response = requests.get(data_endpoint_url)
    if response.status_code == status.HTTP_200_OK:
        return clear_data(response.json())
    else:
        raise ValueError(f"The Status code is different from {status.HTTP_200_OK}, something went wrong.")

def send_data_to_endpoint():
    try:
        log("Prepare to send the send the data to the API gateway")
        data = sense_data()
        url = f"http://{api_gatewat_info['url']}:{api_gatewat_info['port']}"
        requests.post(url=url, json=data)
        log("Data sent to the API gateway")
    except (ValueError, requests.exceptions.JSONDecodeError) as error:
        log(f"An error occurred -> {repr(error)}")

def config_scheduler() -> None:
    log(f"Configuring the scheduler with the following infomrations: Day: {cron_info["day_of_the_week"]}, Hour: {cron_info["hour"]}, Minute: {cron_info["minute"]}")
    if scheduler.running:
        scheduler.shutdown()
    scheduler.add_job(send_data_to_endpoint, "cron",
                day_of_week=cron_info["day_of_the_week"],
                hour=cron_info["hour"],
                minute=cron_info["minute"],
                timezone="UTC"
            )
    log(f"New Cron task configured")
    scheduler.start()


@app.put("/sensor/update/name/{new_name}")
def update_sensor_name(response: Response, new_name: str = name) -> Response:
    log("Received a request to update the Sensor's name")
    if new_name and len(new_name.replace(" ", "")) > 0:
        global name
        name = new_name.replace(" ", "")
        return Response()
    else:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Error: The input name can not be None")
    

@app.put("/sensor/configuration/cron/days")
def update_sensor_date(response: Response, from_day: int = MONDAY, to_day: int = SUNDAY) -> Response:
    if MONDAY <= from_day <= to_day and to_day <= SUNDAY:
        log("Received a request to update the Sensor's days of work")
        cron_info["day_of_the_week"] = f"{from_day}-{to_day}"
        config_scheduler()
        return Response()
    else:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Error: The input days must be in [0, 6]")

@app.put("/sensor/configuration/cron/time")
def update_sensor_time(response: Response, hour: int = MIN_HOUR, minute: int = MIN_MINUTE) -> Response:
    if MIN_HOUR <= hour <= MAX_HOUR and MIN_MINUTE <= minute <= MAX_MINUTE:
        log("Received a new request to update the Sensor's time of work")
        cron_info["hour"] = f"{hour}"
        cron_info["minute"] = f"{minute}"
        config_scheduler()
        response = Response()
    else:
        response = Response(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Error: The input hours must be in [0, 23] and minutes in [0, 59]")
    return response

@app.put("/sensor/configuration/gateway/url")
def update_sensor_gateway_url(response: Response, new_url: str = api_gatewat_info['url']) -> Response:
    if len(new_url) > 0 and len(new_url.replace(' ', '')) > 0:
        log("Received a new request to update the Sensor's gateway url")
        api_gatewat_info['url'] = new_url
        return Response()
    else:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Error: the gateway url should be non empty and should not contains only withe spaces")

@app.put("/sensor/configuration/gateway/port")
def update_sensor_gateway_url(response: Response, port: int = api_gatewat_info['port']) -> Response:
    if 0 <= port <= MAX_PORT:
        log("Received a new request to update the Sensor's gateway url")
        api_gatewat_info['port'] = port
        return Response()
    else:
        return Response(status_code=status.HTTP_406_NOT_ACCEPTABLE, content="Error: the gateway url should be non empty and should not contains only withe spaces")



@app.get("/health")
def health(response: Response) -> Response:
    log("Server pinged")
    return Response(content="Everything is OK.")

@app.get("/info")
def info(response: Response) -> Response:
    log("Returning Sensor information")
    key = "General Sensor Information"
    message: dict[str, list] = defaultdict(list)
    message[key].append({"Sensor Name" : name})
    message[key].append({"Description": description})
    message[key].append({"Endpoint Information" : api_gatewat_info})
    message[key].append({"Cronjob Information": cron_info})
    
    response: Response = Response(content=json.dumps(message))
    response.headers["Content-Type"] = "application/json"
    return response

@app.delete("/shutoff")
def shutoff(response: Response) -> Response:
    log("Shutting off the sensor") 
    try:
        log("Return OK to the client")
        return Response(status_code=200, content='Server shutting down...')
    finally:
        log("exiting...")
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == "__main__":
    config_scheduler()
    register_sensor()
    # register the sensor to the MAIN system
    # start the sensor server
    uvicorn.run(app, host=ip, port=port)