import requests
import json
from ruamel.yaml import YAML
from deepdiff import DeepDiff
import jwt
import time

CONFIG_FILE_NAME = "config.json"
CLIENT_ROLE_FILE_NAME = "client_role_data.yaml"

data = {
    "clients": [],
    "users": []
}

client_map = {}
client_role_map = {}
role_map = {}
role_user_map = {}
user_map = {}


def get_clients(config):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(url, headers=headers)
    # if status code is 2xx, print success message
    if response.status_code // 100 == 2:
        print("Client list retrieved successfully.")
    else:
        print(f"Failed to retrieve client list. Reason: {response.text}")
        exit(1)
    resp_data = response.json()
    client_list = []
    for client in resp_data:
        if client['clientId'].endswith('k8s-api'):
            client_list.append(client)
            client_map[client['clientId']] = client
    return client_list


def get_client_roles(config, client):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients/{client['id']}/roles"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(url, headers=headers)
    resp_data = response.json()
    roles = []
    role_map[client['clientId']] = {}
    for role in resp_data:
        roles.append(role)
        role_map[client['clientId']][role['name']] = role
    return roles


def get_users(config):
    users_url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.get(users_url, headers=headers)
    # if status code is 2xx, print success message
    if response.status_code // 100 == 2:
        print("User list retrieved successfully.")
    else:
        print(f"Failed to retrieve user list. Reason: {response.text}")
        exit(1)
    resp_data = response.json()
    user_list = []
    for user in resp_data:
        user_list.append(user)
        user_map[user['username']] = user
    return user_list


def get_user_role_mapping(base_url, realm, role_name, client_id):
    url = f"{base_url}/auth/admin/realms/{realm}/clients/{client_id}/roles/{role_name}/users"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }

    response = requests.get(url, headers=headers)
    # if status code is 2xx, print success message
    if response.status_code // 100 != 2:
        print(f"Failed to retrieve user role mapping for role {role_name}. Reason: {response.text}")
        exit(1)
    resp_data = response.json()
    user_list = []
    for user in resp_data:
        user_list.append(user)
    return user_list


yaml = YAML(typ='safe')


def read_data_from_file(filename):
    try:
        with open(filename, 'r') as file:
            data = yaml.load(file)
    except FileNotFoundError:
        print(f"Error: file {filename} not found. Run the get_client_role.py python code first.")
        exit(1)

    return data


def read_config_from_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: file {filename} not found. Run the login.py python code first.")
        exit(1)
    return data


def get_remote_data(config):
    data = {
        "clients": [],
        "users": []
    }
    clients = get_clients(config)

    users = get_users(config)
    for client in clients:
        roles = get_client_roles(config, client)
        client_role_map[client['clientId']] = roles
        role_user_map[client['clientId']] = {}
        for role in roles:
            role_user_map[client['clientId']][role['name']] = get_user_role_mapping(config['server_url'], config['organization_id'],
                                                                role['name'], client['id'])
    for user in users:
        data['users'].append({
            "accountId": user['username'],
            "name": user['username']
        })

    i = 0
    for client in clients:
        j = 0
        data['clients'].append({
            "name": client['clientId'],
            "roles": [],
        })
        for role in client_role_map[client['clientId']]:
            data['clients'][i]['roles'].append({
                "name": role['name'],
                "users": []
            })
            for user in role_user_map[client['clientId']][role['name']]:
                data['clients'][i]['roles'][j]['users'].append(user['username'])
            j += 1
        i += 1

    return data


def diff_changes(remote_data, local_data):
    diff = DeepDiff(remote_data, local_data, ignore_order=True, verbose_level=2)
    return diff


def get_value_from_path(data, client_index, path_string):

    # print(data)
    segments = path_string.replace("root", "").replace("][", ".").replace("[", "").replace("]", "").replace("'",
                                                                                                            "").split(
        ".")

    if "roles" in path_string:
        role_name = data['clients'][client_index]['roles'][int(segments[1])]['name']
    else:
        role_name = ""

    return role_name

def get_value_from_path2(data, path_string):

    # print(data)
    segments = path_string.replace("root", "").replace("][", ".").replace("[", "").replace("]", "").replace("'",
                                                                                                            "").split(
        ".")

    client_name = data[segments[0]][int(segments[1])]['name']

    if "roles" in path_string:
        role_name = data[segments[0]][int(segments[1])]['roles'][int(segments[3])]['name']
    else:
        role_name = ""

    return client_name, role_name


def assign_user_to_client_role(config, user, role, client):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/users/{user['id']}/role-mappings/clients/{client['id']}"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}",
        "Content-Type": "application/json"
    }
    payload = json.dumps([{
        "id": role['id'],
        "name": role['name'],
        "composite": False,
        "clientRole": True,
        "containerId": client['id']
    }])
    response = requests.post(url, headers=headers, data=payload)
    # if status code is 2xx, print success message
    if response.status_code // 100 == 2:
        print(f"User {user['username']} assigned to client {client['clientId']} role {role['name']}")
    else:
        print(
            f"Failed to assign user {user['username']} to client {client['clientId']} role {role['name']}. Reason: {response.text}")


def unassign_user_to_client_role(config, user, role, client):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/users/{user['id']}/role-mappings/clients/{client['id']}"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}",
        "Content-Type": "application/json"
    }
    payload = json.dumps([{
        "id": role['id'],
        "name": role['name'],
        "composite": False,
        "clientRole": True,
        "containerId": client['id']
    }])
    response = requests.delete(url, headers=headers, data=payload)
    # if status code is 2xx, print success message
    if response.status_code // 100 == 2:
        print(f"User {user['username']} unassigned to client {client['clientId']} role {role['name']}")
    else:
        print(
            f"Failed to unassign user {user['username']} to client {client['clientId']} role {role['name']}. Reason: {response.text}")


# add keycloak client role
def add_client_role(config, client_id, role_name):
    """Create a new client role in Keycloak."""
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients/{client_id}/roles"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": role_name,
        "composite": False
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 201 or response.status_code == 409:
        print(f"Role {role_name} created successfully.")
    else:
        print(f"Failed to create role {role_name}. Reason: {response.text}")


def delete_client_role(config, client_id, role_name):
    url = f"{config['server_url']}/auth/admin/realms/{config['organization_id']}/clients/{client_id}/roles/{role_name}"
    headers = {
        "Authorization": f"Bearer {config['keycloak_token']}"
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Role {role_name} deleted successfully.")
    else:
        print(f"Failed to delete role {role_name}. Reason: {response.text}")


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

def sort_dict_recursively(d):
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = sort_dict_recursively(value)

    return dict(sorted(d.items()))

if __name__ == "__main__":
    print(f"Reading config... {CONFIG_FILE_NAME}")
    config = read_config_from_file(CONFIG_FILE_NAME)

    if is_token_expired(config['keycloak_token']) or is_token_expired(config['tks_token']):
        print(
            "Token has expired. Please re-login or check if the server and your system's time are synchronized "
            "correctly.")
        exit(1)

    print(f"Reading local data... {CLIENT_ROLE_FILE_NAME}")
    local_data = read_data_from_file(CLIENT_ROLE_FILE_NAME)
    del(local_data['users'])
    # sorted_local_data = sort_dict_recursively(local_data)
    for client in local_data["clients"]:
        client["roles"].sort(key=lambda role: role["name"])
    local_data['clients'].sort(key=lambda client: client['name'])
    get_users(config)

    for client in local_data['clients']:
        for role in client['roles']:
            if 'users' not in role or not isinstance(role['users'], list):
                print(
                    f"'users' field in role '{role['name']}' for client '{client['clientId']}' is missing or null. Please "
                    f"use \'users: []\' to indicate an empty list.")
                exit(1)
            for user in role['users']:
                # if user is not in user_map key
                if user not in user_map:
                    print(f"User {user} not found in keycloak. Please re-check on data.yaml user accountId")
                    exit(1)

    print("Starting client role sync...")
    diff_exist = True
    while diff_exist:
        diff_exist = False
        remote_data = get_remote_data(config)
        del(remote_data['users'])
        for client in remote_data["clients"]:
            client["roles"].sort(key=lambda role: role["name"])
        remote_data['clients'].sort(key=lambda client: client['name'])

        # verifity remote_data and local_data
        if len(remote_data['clients']) != len(local_data['clients']) :
            print("please run get_client_role.py first")
            exit(1)
        for i in range(len(remote_data['clients'])):
            if remote_data['clients'][i]['name'] != local_data['clients'][i]['name']:
                print("please run get_client_role.py first")
                exit(1)

        for i in range(len(remote_data['clients'])):
            client_name = remote_data['clients'][i]['name']
            diff = diff_changes(remote_data['clients'][i], local_data['clients'][i])

            type_paths_and_values = []

            for change_type, changes in diff.items():
                for path, value in changes.items():
                    type_paths_and_values.append((change_type, path, value))

            if len(type_paths_and_values) == 0:
                continue
            diff_exist = True

            for change_type, path, value in type_paths_and_values:
                if change_type == "iterable_item_added":
                    if "users" not in path:
                        # role add
                        role_name = value['name']
                        add_client_role(config, client_map[client_name]['id'], role_name)
                    else:
                        # user add
                        role_name = get_value_from_path(local_data, i, path)
                        user_accountId = value
                        assign_user_to_client_role(config, user_map[user_accountId], role_map[client_name][role_name],
                                                   client_map[client_name])
                elif change_type == "iterable_item_removed":
                    if "users" not in path:
                        role_name = value['name']
                        delete_client_role(config, client_map[client_name]['id'], role_name)
                    else:
                        role_name = get_value_from_path(remote_data, i,  path)
                        user_accountId = value
                        unassign_user_to_client_role(config, user_map[user_accountId], role_map[client_name][role_name],
                                                     client_map[client_name])
                elif change_type == "values_changed":
                    if "roles" not in path:
                        old_roles = value['old_value']['roles']
                        new_roles = value['new_value']['roles']
                        old_roles_name = []
                        new_roles_name = []
                        for old_role in old_roles:
                            old_roles_name.append(old_role['name'])
                        for new_role in new_roles:
                            new_roles_name.append(new_role['name'])

                        new_role_list = set(new_roles_name) - set(old_roles_name)
                        old_role_list = set(old_roles_name) - set(new_roles_name)

                        for new_role in new_role_list:
                            add_client_role(config, client_map[client_name]['id'], new_role)
                        for old_role in old_role_list:
                            delete_client_role(config, client_map[client_name]['id'], old_role)
                        continue

                    if "users" not in path:
                        role_name = get_value_from_path(remote_data, i, path)
                        if "name" in value['new_value'] and "name" in value['old_value']:
                            if value['new_value']['name'] == value['old_value']['name']:
                                old_user_accountIds = value['old_value']['users']
                                new_user_accountIds = value['new_value']['users']
                                new_user_list = set(new_user_accountIds) - set(old_user_accountIds)
                                old_user_list = set(old_user_accountIds) - set(new_user_accountIds)

                                for new_user_accountId in new_user_list:
                                    assign_user_to_client_role(config, user_map[new_user_accountId], role_map[client_name][role_name],
                                                               client_map[client_name])
                                for old_user_accountId in old_user_list:
                                    unassign_user_to_client_role(config, user_map[old_user_accountId], role_map[client_name][role_name],
                                                             client_map[client_name])
                                continue

                        if "name" in value['new_value']:
                            new_role_name = value['new_value']['name']
                        else:
                            new_role_name = value['new_value']
                        if "name" in value['old_value']:
                            old_role_name = value['old_value']['name']
                        else:
                            old_role_name = value['old_value']
                        delete_client_role(config, client_map[client_name]['id'], old_role_name)
                        add_client_role(config, client_map[client_name]['id'], new_role_name)

                    else:
                        client_name, role_name = get_value_from_path(remote_data, path)
                        old_user_accountId = value['old_value']
                        new_user_accountId = value['new_value']

                        assign_user_to_client_role(config, user_map[new_user_accountId], role_map[client_name][role_name],
                                                   client_map[client_name])
                        unassign_user_to_client_role(config, user_map[old_user_accountId], role_map[client_name][role_name],
                                                     client_map[client_name])
            time.sleep(1)

    print("Client role sync completed.")
