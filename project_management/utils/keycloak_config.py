KEYCLOAK_CONFIG = {
    "server_url": "https://keycloak.desp-aas.acri-st.fr/auth/admin",
    "admin_username": "desp-service",
    "admin_password": "#AcriDESP2024",
    "master_realm": "master",
    "default_realm": "projects",
    "verify_ssl": True
}

# Template for client representation
CLIENT_REPRESENTATION_TEMPLATE = {
    "clientId": "sandbox-client",
    "enabled": True,
    "protocol": "openid-connect",
    "publicClient": True,
    "redirectUris": ["http://localhost:8080/*"],
    "webOrigins": ["http://localhost:8080"],
    "standardFlowEnabled": True,
    "implicitFlowEnabled": False,
    "directAccessGrantsEnabled": True,
    "serviceAccountsEnabled": False,
    "authorizationServicesEnabled": False,
    "attributes": {
        "backchannel.logout.session.required": "true",
        "backchannel.logout.revoke.offline.tokens": "false"
    }
}
