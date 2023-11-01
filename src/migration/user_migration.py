import requests
import json

DEFAULT_PASSWORD: str = "password"


def migrate_users(config, users):
    print(f"Migrating {len(users)} users...")
    created_user_list = []
    for user in users:

        url = f"{config['keycloak']['keycloak_url']}/api/1.0/organizations/{config['tks']['organization_id']}/users"
        headers = {
            "Content-Type": "text/plain",
            "Authorization": f"Bearer {config['tks']['tks_token']}"
        }

        first_name = user.get("firstName")
        last_name = user.get("lastName")
        name = (first_name or "") + (last_name or "") or user['username']

        payload = """{"accountId": "%s", "password": "%s", "name": "%s", "email": "%s", "role" : "user"}""" % (
            user['username'] + user['username'], DEFAULT_PASSWORD, name, user['username'] + user['email'])


        created_user_list.append({
            "accountId": user['username'],
            "name": name,
            "email": user['username'] + user['email'],
            "password": DEFAULT_PASSWORD,
            "role": "user"
        })
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 201 and response.status_code != 409:
            raise Exception(f"Failed to get token. Response: {response.text}")


    print(json.dumps(created_user_list, indent=4, sort_keys=True))

    return


def load_users_from_file(filename):
    with open(filename, 'r') as file:
        user_list = json.load(file)
    return user_list


def read_config_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data


if __name__ == "__main__":
    config = read_config_from_file("config.json")
    users = load_users_from_file("users.json")
    migrate_users(config, users)
