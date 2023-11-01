import requests
import json
import getpass


def get_keycloak_token(base_url, realm, username, password):
    token_url = f"{base_url}/auth/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "client_id": "admin-cli",
        "username": username,
        "password": password,
        "grant_type": "password"
    }

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to get token. Response: {response.text}")

    data = response.json()
    return data['access_token']


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


def save_token_to_file(conf, filename):
    with open(filename, 'w') as file:
        json.dump(conf, file, indent=4)


def load_config_from_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data


def validate_format(data):
    if "keycloak" not in data or "tks" not in data:
        return False

    keycloak_keys = ["server_url", "realm_id", "token"]
    tks_keys = ["server_url", "organization_id", "token"]

    for key in keycloak_keys:
        if key not in data["keycloak"] or not data["keycloak"][key]:
            return False

    for key in tks_keys:
        if key not in data["tks"] or not data["tks"][key]:
            return False

    return True


if __name__ == "__main__":
    config_dict = load_config_from_file("./config.json")


    Login_TARGET = input("Login target (keycloak or tks): ")
    while Login_TARGET not in ["keycloak", "tks"]:
        Login_TARGET = input("Login target (keycloak or tks): ")
    if Login_TARGET == "keycloak":
        SERVER_URL = input("Please enter the keycloak URL: ")
        while SERVER_URL == "":
            SERVER_URL = input("Please enter the keycloak URL: ")
        if SERVER_URL[-1] == "/":
            SERVER_URL = SERVER_URL[:-1]
        if SERVER_URL[-5:] == "/auth":
            SERVER_URL = SERVER_URL[:-5]
        config_dict["keycloak"]["keycloak_url"] = SERVER_URL

        REALM_ID = input("Please enter the realm id: ")
        while REALM_ID == "":
            REALM_ID = input("Please enter the realm id: ")
        config_dict["keycloak"]["realm_id"] = REALM_ID

        USERNAME = input("Please enter your username: ")
        while USERNAME == "":
            USERNAME = input("Please enter your username: ")

        PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")
        while USERNAME == "":
            PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")
    else:
        SERVER_URL = input("Please enter the TKS URL: ")
        while SERVER_URL == "":
            SERVER_URL = input("Please enter the TKS URL: ")
        if SERVER_URL[-1] == "/":
            SERVER_URL = SERVER_URL[:-1]
        config_dict["tks"]["tks_url"] = SERVER_URL

        ORGANIZATION_ID = input("Please enter the organization name: ")
        while ORGANIZATION_ID == "":
            ORGANIZATION_ID = input("Please enter the organization name: ")
        config_dict["tks"]["organization_id"] = ORGANIZATION_ID

        USERNAME = input("Please enter your username: ")
        while USERNAME == "":
            USERNAME = input("Please enter your username: ")

        PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")
        while USERNAME == "":
            PASSWORD = getpass.getpass("비밀번호를 입력하세요: ")

    # Get the token and save it to a file
    try:
        if Login_TARGET == "tks":
            config_dict["tks"]["tks_token"] = get_tks_token(SERVER_URL, ORGANIZATION_ID, USERNAME, PASSWORD)
        else:
            config_dict["keycloak"]["keycloak_token"] = get_keycloak_token(SERVER_URL, REALM_ID, USERNAME, PASSWORD)

    except Exception as e:
        print(e)
        exit(1)
    save_token_to_file(config_dict, "./config.json")
    print("Token saved to ./config.json")
