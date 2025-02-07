# er-climate-monitor-sensors
Submodule of [Er-Climate-Monitor](https://github.com/MatteoIorio11/er-climate-monitor) repository.

**Software Process Engineering** and **Web Application and Services** courses' projects.

## Usage
1. Configure your sensor building the yaml file (take as reference `sensor/configuration.yaml`)
3. Inside `./sensor`, run `uv sync` or manually install all dependencies
4. Run `python create_template.py <YourSensorConfig>.yaml`
5. Go back to the project root
6. Run `python -m python -m sensor.sensor_<generated-sensor-name>`
