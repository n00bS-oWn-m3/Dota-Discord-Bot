import json
# All helper-commands related to manipulating JSON files

# Load a given JSON-file
def get_json(json_file):
    with open(f"resources/json_files/{json_file}", "r") as f:
        return json.load(f)


# Update a given JSON-file
def update_json(json_file, data):
    with open(f"resources/json_files/{json_file}", "w") as f:
        json.dump(data, f, indent=4)


def refresh_usermapping():  # Might change due to register command so we want to be able to refresh it
    with open('resources/json_files/usermapping.json', 'r') as f:
        global usermapping
        usermapping = json.load(f)