import yaml
from jinja2 import Template
from collections import defaultdict

print("Reading the configuration File...")
configuration_content = ""
with open("configuration.yaml") as file:
    configuration_content = file.read()
yaml_file = yaml.safe_load(configuration_content)
values = defaultdict(str)
print("Now We have to create the map key-value, used for the template replacing.")

def dfs(key, node):
    if type(node) != dict or len(node) == 0:
        values[key] = node if type(node) != str else node.replace(" ", "")
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
with open(f"sensor_{values["SENSOR_INFORMATION_NAME"].replace(" ", "")}.py", "w") as file:
    file.write(new_content)