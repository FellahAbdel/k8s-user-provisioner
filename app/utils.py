import string
import random
import os
import yaml
from keycloak import KeycloakAdmin
from kubernetes import client, config, utils


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


def create_keycloak_user(email):

    KEYCLOAK_BASE_URL = os.environ.get('KEYCLOAK_BASE_URL')
    REALM = os.environ.get('KEYCLOAK_REALM')
    CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET')

    username = email.split('@')[0]

    keycloak_admin = KeycloakAdmin(
        server_url=KEYCLOAK_BASE_URL,
        client_id=CLIENT_ID,
        client_secret_key=CLIENT_SECRET,
        realm_name=REALM,
        verify=True
    )

    generated_password = generate_password()

    user_data = {
        'email': email,
        'enabled': True,
        'username': username,
        'credentials': [{'type': 'password', 'value': generated_password}]
    }

    user_id = keycloak_admin.get_user_id(username)

    if not user_id:
        keycloak_admin.create_user(user_data, exist_ok=True)

    user_id = keycloak_admin.get_user_id(username)

    return user_id, generated_password


def apply_k8s_config(username, user_id):

    k8s_file = 'k8s_templates/provisionner.yaml'

    template = None

    with open(k8s_file) as f:
        template = f.read()

    template.replace("{{username}}", username)
    template.replace("{{user_id}}", user_id)

    template = yaml.safe_load(template)

    config.load_kube_config()
    k8s_client = client.ApiClient()

    utils.create_from_dict(k8s_client, template)

    return True
