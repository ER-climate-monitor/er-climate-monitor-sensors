# er-climate-monitor-sensors
Submodule of [Er-Climate-Monitor](https://github.com/MatteoIorio11/er-climate-monitor) repository.

**Software Process Engineering** and **Web Application and Services** courses' projects.

## Usage

### Way 1 (DSL)
You can use the [sensor's configuration Domain Specific Language](https://github.com/ER-climate-monitor/er-climate-monitor-dsl) in order to
build and produce a valid sensor script (`sensor_.*py` file). You can follow the instructions [here](https://github.com/ER-climate-monitor/er-climate-monitor-sensors/blob/main/dsl-sensor-generator/README.md) for more information on how to use the generator and produce such scirpt.

After you've succesfully craeted you sensor script:
1. place the script it inside the `sensor/` directory and install required dependency (or just `uv sync`);
2. Go back to the project root
3. Run `python -m python -m sensor.sensor_<generated-sensor-name>`

### Way 2 (YAML)
1. Configure your sensor building the yaml file (take as reference `sensor/configuration.yaml`)
3. Inside `./sensor`, run `uv sync` or manually install all dependencies
4. Run `python create_template.py <YourSensorConfig>.yaml`
5. Go back to the project root
6. Run `python -m python -m sensor.sensor_<generated-sensor-name>`
