import yaml
from jinja2 import Template
from collections import defaultdict
import sys

if len(sys.argv) != 2:
    print("Usage: python create_template.py <config_file.yaml>")
    sys.exit(1)

config_file = sys.argv[1]

print(f"Reading the configuration File: '{config_file}'")
configuration_content = ""
with open(config_file) as file:
    configuration_content = file.read()
yaml_file = yaml.safe_load(configuration_content)
values = defaultdict(str)
print("Now We have to create the map key-value, used for the template replacing.")

def check_for_node(key_name: str, node):
    if type(node) == int and node < 0:
        raise ValueError(f"Information at: {key_name} can not be negative, fix this error.")
    elif type(node) == str and (len(node) == 0 or len(node.replace(" ", "")) == 0):
        raise ValueError(f"String type information at: {key_name} can not be null and It should contain at least one char")
    return node

def dfs(key, node):
    if type(node) != dict or len(node) == 0:
        values[key] = check_for_node(key, node)
        print(f"Key: {key}, Value: {node}")
        return
    for name in node.keys():
        dfs(key + ("_" if len(key) > 0 else "") + name.upper(), node[name])
    
dfs("", yaml_file)
with open("sensor_template.py") as file:
    configuration_content = file.read()
print("Replace all the information inside the template file.")
template = Template(configuration_content)
new_content = template.render(**values)

sensor_name = values["SENSOR_INFORMATION_NAME"].replace(" ", "")
sensor_type = values["SENSOR_INFORMATION_TYPE"]
with open(f"sensor_{sensor_type}_{sensor_name}.py", "w") as file:
    file.write(new_content)

