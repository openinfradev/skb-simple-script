import requests
import json
import yaml
import jwt
import time

CONFIG_FILE_NAME = "config.json"
CLIENT_ROLE_FILE_NAME = "client_role_data.yaml"

def get_clients(config):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(url, headers=headers)
    resp_data = response.json()
    client_list = []
    for client in resp_data:
        if client['clientId'].endswith('-k8s-api'):
            client_list.append(client)
    return client_list

def get_client_roles(config, client):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients/{client['id']}/roles"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(url, headers=headers)
    resp_data = response.json()
    roles = []
    for role in resp_data:
        roles.append(role)
    return roles

def get_users(config):
    users_url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(users_url, headers=headers)
    resp_data = response.json()
    user_list = []
    for user in resp_data:
        user_list.append(user)
    return user_list

def get_user_role_mapping(base_url, realm, role_name, client_id):
    url = f"{base_url}/auth/admin/realms/{realm}/clients/{client_id}/roles/{role_name}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }

    response = requests.get(url, headers=headers)
    resp_data = response.json()
    user_list = []
    for user in resp_data:
        user_list.append(user)
    return user_list



def load_users_from_file(filename):
    with open(filename, 'r') as file:
        user_list = json.load(file)
    return user_list


def read_config_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def get_remote_data(config):
    data = {
        "clients": [],
        "users": []
    }

    client_map = {}
    role_map = {}

    clients = get_clients(config)
    users = get_users(config)
    for client in clients:
        roles = get_client_roles(config, client)
        client_map[client['clientId']] = roles
        role_map[client['clientId']] = {}
        for role in roles:
            role_map[client['clientId']][role['name']] = get_user_role_mapping(config['server_url'], config['organization_id'], role['name'], client['id'])
    for user in users:
        data['users'].append({
            "accountId": user['username'],
            "name": user['firstName']
        })

    i = 0
    for client in clients:
        j = 0
        data['clients'].append({
            "name": client['clientId'],
            "roles": [],
        })
        for role in client_map[client['clientId']]:
            data['clients'][i]['roles'].append({
                "name": role['name'],
                "users": []
            })
            for user in role_map[client['clientId']][role['name']]:
                data['clients'][i]['roles'][j]['users'].append(user['username'])
            j += 1
        i += 1

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

    print(f"Retrieving data from keycloak")
    data = get_remote_data(config)

    print(f"Data saved to {CLIENT_ROLE_FILE_NAME}")
    with open(CLIENT_ROLE_FILE_NAME, 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file, indent=2, sort_keys=True, allow_unicode=True)






