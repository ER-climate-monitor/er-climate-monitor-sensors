#!/usr/bin/env python3

import yaml
import random
import os
import sys
import subprocess
import logging

logger = logging.getLogger('TempalteCreator')

selected_sensors = {
    "idro_level": [
        "Diga di Ridracoli",
        "Castelbolognese",
        "Ponte degli Alpini",
        "S. Carlo",
        "Ponte Nibbiano Tidoncello"
    ],
    "temp": [
        "Sestola",
        "Cesenatico porto",
        "Piacenza urbana",
        "Cesena urbana",
        "S. Marino",
        "Bologna San Luca",
        "Lavezzola"
    ],
    "humidity": [
        "Carpineta",
        "Cesena urbana",
        "Reggio nell'Emilia urbana",
        "Novafeltria",
        "Mirabello",
        "Rimini urbana",
        "Piacenza urbana"
    ],
    "wind": [
        "Bologna urbana",
        "Reggio nell'Emilia urbana",
        "GIRALDA",
        "S. Pietro Capofiume",
        "Martorano",
        "Madonna dei Fornelli",
        "Modena urbana",
        "Bologna Torre Asinelli"
    ],
    "rain": [
        "S. Felice sul Panaro",
        "Madonna dei Fornelli",
        "Bologna San Luca",
        "Paderno",
        "Secondo Salto",
        "Castel San Pietro Arpa",
        "S. Cassiano sul Lamone",
        "Premilcuore",
        "Castrocaro",
        "S. Maria Nova"
    ]
}

def generate_sensor_config(name: str, sensor_type: str, port: int, ip: str) -> dict:
    queries = ["soglia1", "soglia2", "soglia3"] if sensor_type != 'rain' else []
    return {
        "sensor": {
            "information": {
                "name": name,
                "description": "General Sensor Description",
                "type": sensor_type,
                "queries": queries,
            },
            "ethernet": {
                "port": port,
                "ip": ip
            },
            "registry": {
                "url": "http://127.0.0.1:3000/v0/api/sensor",
                "registerPath": "/register",
                "shutDownPath": "/shutdown",
                "key": "secretKey"
            },
            "apiGateway": {
                "url": "localhost",
                "port": 3000
            },
            "cronjob": {
                "day_of_week": "0-6",
                "hour": "*",
                "minute": "*"
            }
        }
    }

def create_config_files(directory: str):
    logger.info('Creating config file for sensor samples')
    num_sensors = sum(map(lambda x: len(x), selected_sensors.values()))
    print(num_sensors)
    # ips = [ f'122.178.101.{n}' for n in random.sample(range(1, 255), num_sensors) ]
    ports = random.sample(range(12000, 20000), num_sensors)

    i = 0
    for sensor_type, sensor_names in selected_sensors.items():
        for sensor_name in sensor_names:
            sensor_name = sensor_name.replace(' ', '')
            config = generate_sensor_config(sensor_name, sensor_type, ports[i], '0.0.0.0')
            output_file = os.path.join(directory, f'sensor_{sensor_type}_{sensor_name}.yaml')
            with open(output_file, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Config for sensor '{sensor_name}' of type {sensor_type} has been created succesfully at: {output_file}")
            i += 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    directory = 'sensors_config'
    if (not os.path.exists(directory) or not os.listdir(directory)):
        logger.info(f'Directory: {directory} has not been found or it is empty')
        os.makedirs(directory, exist_ok=True)
        create_config_files(directory)
    else:
        logger.info(f'files in directory {directory} have been already created')

    if len(sys.argv) > 1:
        if sys.argv[1] == 'create':
            logger.info('Creating sensors from yaml specifications')
            yaml_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.yaml')]
            for yaml_file in yaml_files:
                logger.info(f'Procesing {yaml_file}')
                subprocess.run(['python3', 'create_template.py', yaml_file], stdout=subprocess.DEVNULL)
        elif sys.argv[1] == 'clear':
            logger.info('clearing all generated sensors')
            all_sensors = [sensor.replace(' ', '') for sensors in selected_sensors.values() for sensor in sensors]
            files_to_delete = [file for file in os.listdir() if any(sensor in file for sensor in all_sensors) and file != 'sensor_template.py']
            for file in files_to_delete:
                os.remove(file)
            logger.info('Cleanup complete!')
    else:
        logger.info("No <create> option has been provided, doing nothing...")
