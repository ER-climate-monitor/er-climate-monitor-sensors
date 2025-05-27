# DSL Sensor Generator

Simple python web server that integrates a web editor with an integrated LSP for the Domain Specific Language for Sensors configuration,
while providing the ability to convert right away `.uanciutri` files into compliant python executable scripts.

## Usage

> Note: If possbile, try to use a python virtual environment (`python -m venv .venv` and activate with `source .venv/bin/activate`)

If you have `uv` installed in your system, just `uv sync`, or else install requiremets with `pip install -r requirements.txt`.

You can run the python server simply with `python main.py` or `uv run` and visit [localhost:8080](http://localhost:8080).

In order to use the sensor config generator:

1. Wait until the bottom right button enables, this will let you visit the sensor config editor with the integrated LSP;
2. Once your sensor config are finished, copy the code from the Sensor Config Editor and paste it in the main applicaiton text area;
3. Click on generate;
4. Once generation has completed, you'll find the `<your-sensor-config>.uanciutri` file and its associated `sensor_<your-sensor-config>.py` script.
5. Place it inside the `<path-to-repo-root>/sensors/` and follow the usual instructions for running a sensor.

