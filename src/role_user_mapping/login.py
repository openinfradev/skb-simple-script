import requests
import json
import getpass


def get_tks_token(tks_url, organization_id, account_id, password):
    token_url = f"{tks_url}/api/1.0/auth/login"
    payload = """
    {
        "organizationId": "%s",
        "accountId": "%s",
        "password": "%s"
    }
    """ % (organization_id, account_id, password)

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to get token. Response: {response.text}")

    data = response.json()
    return data['user']['token']


def get_keycloak_token(base_url, realm, client_id, username, password):
    token_url = f"{base_url}/auth/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "client_id": client_id,
        "username": username,
        "password": password,
        "grant_type": "password"
    }

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to get token. Response: {response.text}")

    data = response.json()
    return data['access_token']


def save_token_to_file(conf, filename):
    with open(filename, 'w') as file:
        json.dump(conf, file, indent=4)


if __name__ == "__main__":
    TKS_URL = "https://tks-console-dev.taco-cat.xyz"
    BASE_URL = "https://tks-console-dev.taco-cat.xyz"
    CLIENT_ID = "admin-cli"

    config_dict = {}

    SERVER_URL = input("Please enter the server URL: ")
    while SERVER_URL == "":
        SERVER_URL = input("Please enter the server URL: ")
    config_dict["server_url"] = SERVER_URL

    ORGANIZATION_ID = input("Please enter the organization name: ")
    while ORGANIZATION_ID == "":
        ORGANIZATION_ID = input("Please enter the organization name: ")
    config_dict["organization_id"] = ORGANIZATION_ID

    USERNAME = input("Please enter your username: ")
    while USERNAME == "":
        USERNAME = input("Please enter your username: ")

    PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")
    while USERNAME == "":
        PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")

    if SERVER_URL[-1] == "/":
        SERVER_URL = SERVER_URL[:-1]

    # Get the token and save it to a file
    try:
        keycloak_token = get_keycloak_token(BASE_URL, ORGANIZATION_ID, CLIENT_ID, USERNAME, PASSWORD)
        config_dict["keycloak_token"] = keycloak_token
        tks_token = get_tks_token(TKS_URL, ORGANIZATION_ID, USERNAME, PASSWORD)
        config_dict["tks_token"] = tks_token
    except Exception as e:
        print(e)
        exit(1)
    save_token_to_file(config_dict, "config.json")
    print("Token saved to ./config.json")
