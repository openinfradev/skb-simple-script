import requests
import json
import jwt
import time


CONFIG_FILE_NAME = "config.json"
USER_FILE_NAME = "users.json"

def get_users(config):
    users_url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
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


def is_token_expired(token):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        current_time = time.time()
        expiration_time = payload['exp']

        return current_time > expiration_time

    except jwt.ExpiredSignatureError:
        return True
    except Exception as e:
        print(f"Token validation error: {e}")
        return True


if __name__ == "__main__":
    print(f"Reading config... {CONFIG_FILE_NAME}")
    config = read_config_from_file(CONFIG_FILE_NAME)

    if is_token_expired(config['keycloak_token']) or is_token_expired(config['tks_token']):
        print(
            "Token has expired. Please re-login or check if the server and your system's time are synchronized "
            "correctly.")
        exit(1)

    print(f"Listing users in {config['organization_id']} realms...")
    users = get_users(config)
    print(f"Saving users in {config['organization_id']} realms to file {USER_FILE_NAME}...")
    save_users_to_file(users, USER_FILE_NAME)
