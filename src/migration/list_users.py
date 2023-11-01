import requests
import json


def get_users(config):
    users_url = f"{config['keycloak']['keycloak_url']}/auth/admin/realms/{config['keycloak']['realm_id']}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak']['keycloak_token']}"
    }

    response = requests.get(users_url, headers=headers)
    return response.json()

def save_users_to_file(users, filename):
    with open(filename, 'w') as file:
        json.dump(users, file, indent=4)
        print("Users saved to users.json")


def read_config_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data


if __name__ == "__main__":
    config = read_config_from_file("config.json")
    users = get_users(config)
    print(f"{len(users)} users found.")
    save_users_to_file(users, "users.json")
