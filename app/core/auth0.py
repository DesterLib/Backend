import re
import jwt
import httpx
import os.path
import ujson as json
from time import time
from app import logger
from fastapi import status
from functools import wraps
from json import JSONDecodeError
from dataclasses import dataclass
from typing import Any, Dict, Optional
from fastapi.responses import UJSONResponse
from httpx import HTTPError, InvalidURL, RequestError


@dataclass
class Token:
    access_token: str
    token_expiry: Optional[str] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "Token":
        return cls(**json)

    def to_json(self) -> Dict[str, Any]:
        return self.__dict__()

    def __dict__(self):
        return {"access_token": self.access_token, "token_expiry": self.token_expiry}


class Auth0Manager:
    def __init__(
        self,
        domain: str,
        mtm_client_id: str,
        mtm_client_secret: str,
        fqdn: str,
    ) -> None:
        self.domain = domain
        self.mtm_client_id = mtm_client_id
        self.mtm_client_secret = mtm_client_secret
        self.base_url = f"https://{domain}"
        self.grant_type = "client_credentials"  # OAuth 2.0 flow to use
        self.audience = f"{self.base_url}/api/v2/"
        self.api_identifier = fqdn
        if not re.search(r"https?://", fqdn):
            self.api_identifier = (
                f"http{'s' if not fqdn.startswith('localhost') else ''}://{fqdn}"
            )
        self.httpx = httpx.Client()
        self.token = self.get_access_token()
        self.httpx.headers.update(
            {
                "Authorization": f"Bearer {self.token.access_token}",
                "Content-Type": "application/json",
            }
        )

    def request_access_token(self) -> Token:
        logger.debug("Requesting access token...")
        for c in range(4):
            if not c == 0:
                logger.debug(f"Retrying ({c}) ...")
            try:
                data = {
                    "grant_type": self.grant_type,
                    "client_id": self.mtm_client_id,
                    "client_secret": self.mtm_client_secret,
                    "audience": self.audience,
                }
                response = self.httpx.post(f"{self.base_url}/oauth/token", data=data)
                res = response.json()
            except (HTTPError, RequestError, InvalidURL) as e:
                raise e
            except JSONDecodeError:
                pass
            else:
                token = Token(
                    res["access_token"], token_expiry=time() + int(res["expires_in"])
                )
                return token
        else:
            exit("Failed to get access token")

    def get_access_token(self, bypass_old_token: bool = True) -> Token:
        if not os.path.exists("cache/access_token.json") or bypass_old_token:
            token = self.request_access_token()
            json.dump(token.to_json(), open("cache/access_token.json", "w"))
        else:
            try:
                token = json.load(open("cache/access_token.json"))
                token = Token.from_json(token)
                if token.token_expiry < time():
                    token = self.request_access_token()
                    json.dump(token.to_json(), open("cache/access_token.json", "w"))
            except ValueError:
                token = self.request_access_token()
                json.dump(token.to_json(), open("cache/access_token.json", "w"))
        self.token = token
        return token

    @property
    def clients(self) -> Dict[str, Any]:
        response = self.httpx.get(f"{self.base_url}/api/v2/clients")
        return response.json()

    def get_client(self, client_id: str) -> Dict[str, Any]:
        response = self.httpx.get(f"{self.base_url}/api/v2/clients/{client_id}")
        return response.json()

    def create_client(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.httpx.post(f"{self.base_url}/api/v2/clients", json=data)
        return response.json()

    def update_client(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.httpx.patch(
            f"{self.base_url}/api/v2/clients/{client_id}", json=data
        )
        return response.json()

    @property
    def client_grants(self):
        response = self.httpx.get(
            f"{self.base_url}/api/v2/client-grants",
            params={
                "client_id": self.mtm_client_id,
                "audience": self.audience,
            },
        )
        return response.json()

    def create_client_grant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.httpx.post(f"{self.base_url}/api/v2/client-grants", json=data)
        return response.json()

    def update_client_grant(
        self, client_grant_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = self.httpx.patch(
            f"{self.base_url}/api/v2/client-grants/{client_grant_id}", json=data
        )
        return response.json()

    def delete_client_grant(self, client_grant_id: str):
        response = self.httpx.delete(
            f"{self.base_url}/api/v2/client-grants/{client_grant_id}"
        )
        return response.json()

    @property
    def resource_servers(self):
        response = self.httpx.get(f"{self.base_url}/api/v2/resource-servers")
        return response.json()

    def get_resource_server(self, server_id: str) -> Dict[str, Any]:
        response = self.httpx.get(
            f"{self.base_url}/api/v2/resource-servers/{server_id}"
        )
        return response.json()

    def create_resource_server(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.httpx.post(
            f"{self.base_url}/api/v2/resource-servers", json=data
        )
        return response.json()

    def update_resource_server(
        self, server_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = self.httpx.patch(
            f"{self.base_url}/api/v2/resource-servers/{server_id}", json=data
        )
        return response.json()

    def initialize_global_client_grants(self):
        required_scopes = [
            "read:client_credentials",
            "read:clients",
            "update:clients",
            "create:clients",
            "delete:clients",
            "read:client_grants",
            "create:client_grants",
            "delete:client_grants",
            "update:client_grants",
            "read:resource_servers",
            "create:resource_servers",
            "update:resource_servers",
            "delete:resource_servers",
        ]
        client_grants = self.client_grants
        if "error" in client_grants:
            exit(
                "Seems like you haven't given the mandatory scopes to the machine-to-machine [MTM] application, \
                   Please delete the current MTM application and create one again with the mandatory scopes \
                   ['read:client_grants', 'create:client_grants', 'delete:client_grants', 'update:client_grants'] and update the client_id and client_secret."
            )
        for grant in self.client_grants:
            if grant["client_id"] == self.mtm_client_id:
                logger.debug("Found the grant")
                if not set(grant["scope"]) == set(required_scopes):
                    logger.debug("Insufficient scopes, updating..")
                    resp = self.update_client_grant(
                        grant["id"], {"scope": required_scopes}
                    )
                    if "error" in resp:
                        logger.debug(resp)
                        exit("Error while updating the client grant")
                break
        else:
            logger.debug("No grants found, creating one..")
            self.create_client_grant(
                {
                    "client_id": self.mtm_client_id,
                    "audience": self.audience,
                    "scope": required_scopes,
                }
            )

    def initialize_api(self):
        self.initialize_global_client_grants()
        required_scopes = ["read:current_user"]
        resource_servers = self.resource_servers
        if "error" in resource_servers:
            self.get_access_token(True)
            resource_servers = self.resource_servers
        for api in resource_servers:
            if (
                api.get("name") == "Dester"
                and api.get("identifier") == self.api_identifier
            ):
                logger.debug("Found the api")
                if not api.get("signing_alg") == "RS256":
                    logger.debug("Signing algorithm is incorrect, updating..")
                    api = self.update_resource_server(
                        api["id"], {"signing_alg": "RS256"}
                    )
                if not set([obj.get("value") for obj in api.get("scopes", [])]) == set(
                    required_scopes
                ):
                    logger.debug("Insufficient scopes, updating..")
                    api = self.update_resource_server(
                        api["id"],
                        {
                            "scopes": [
                                {
                                    "value": scope,
                                    "description": f"Auto-added scope [{scope}]",
                                }
                                for scope in required_scopes
                            ]
                        },
                    )
                if not api.get("enforce_policies"):
                    logger.debug("Enforcing policies is disabled, updating..")
                    api = self.update_resource_server(
                        api["id"], {"enforce_policies": True}
                    )
                if not api.get("skip_consent_for_verifiable_first_party_clients"):
                    logger.debug(
                        "Consent for verifiable first party clients is disabled, updating.."
                    )
                    api = self.update_resource_server(
                        api["id"],
                        {"skip_consent_for_verifiable_first_party_clients": True},
                    )
                if not api.get("enforce_policies"):
                    logger.debug("Enforcing policies is disabled, updating..")
                    api = self.update_resource_server(
                        api["id"], {"enforce_policies": True}
                    )
                break
        else:
            logger.debug("No api found, creating one..")
            api = self.create_resource_server(
                {
                    "name": "Dester",
                    "identifier": self.api_identifier,
                    "signing_alg": "RS256",
                    "scopes": [
                        {"value": scope, "description": f"Auto-added scope [{scope}]"}
                        for scope in required_scopes
                    ],
                    "enforce_policies": True,
                    "token_dialect": "access_token_authz",
                    "skip_consent_for_verifiable_first_party_clients": True,
                }
            )
        for client in self.clients:
            if (
                client.get("app_type") == "non_interactive"
                and client.get("name") == "Dester [API]"
            ):
                logger.debug("Found the mtm client")
                mtm_client_id = client["client_id"]
                if not client.get("token_endpoint_auth_method") == "client_secret_post":
                    logger.debug("Updating auth method..")
                    client = self.update_client(
                        mtm_client_id,
                        {"token_endpoint_auth_method": "client_secret_post"},
                    )
                if not client.get("oidc_conformant"):
                    logger.debug("Updating oidc conformant..")
                    client = self.update_client(
                        mtm_client_id, {"oidc_conformant": True}
                    )
                if not client.get("grant_types") == ["client_credentials"]:
                    logger.debug("Updating grant types..")
                    client = self.update_client(
                        mtm_client_id, {"grant_types": ["client_credentials"]}
                    )
                break
        else:
            logger.debug(
                f"No machine-to-machine APP found for API '{api.get('name')}', creating one.."
            )
            client = self.create_client(
                {
                    "app_type": "non_interactive",
                    "name": "Dester [API]",
                    "jwt_configuration": {
                        "alg": "RS256",
                        "lifetime_in_seconds": 3600,
                    },
                    "grant_types": ["client_credentials"],
                    "token_endpoint_auth_method": "client_secret_post",
                    "oidc_conformant": True,
                }
            )
            self.update_client_grant(
                client.get("client_id"),
                {"audience": self.audience, "scope": ["read:current_user"]},
            )
        return client

    def get_spa_client(self) -> Dict[str, Any]:
        self.initialize_global_client_grants()
        for client in self.clients:
            if client.get("app_type") == "spa":
                logger.debug("Found the client")
                spa_client_id = client["client_id"]
                if client.get("callbacks") != [self.api_identifier]:
                    logger.debug("Updating callbacks..")
                    client = self.update_client(
                        spa_client_id, {"callbacks": [self.api_identifier]}
                    )
                if client.get("web_origins") != [self.api_identifier]:
                    logger.debug("Updating web origins..")
                    client = self.update_client(
                        spa_client_id, {"web_origins": [self.api_identifier]}
                    )
                if client.get("allowed_logout_urls") != [self.api_identifier]:
                    logger.debug("Updating allowed logout urls..")
                    client = self.update_client(
                        spa_client_id, {"allowed_logout_urls": [self.api_identifier]}
                    )
                break
        else:
            logger.debug("No single page app client found, creating one..")
            client = self.create_client(
                {
                    "app_type": "spa",
                    "name": "Single Page App [Dester]",
                    "callbacks": [self.api_identifier],
                    "web_origins": [self.api_identifier],
                    "allowed_logout_urls": [self.api_identifier],
                }
            )
        return client


if __name__ == "__main__":
    domain = input("Enter your domain: ")
    if not domain:
        domain = "among.us.auth0.com"
    global_client_id = input("Enter your global client id:> ")
    if not global_client_id:
        global_client_id = "6d3j9xHp1JMEr5TW591C6vuiBMQJoEIt"
    global_client_secret = input("Enter your global client secret:> ")
    if not global_client_secret:
        global_client_secret = (
            "-fpIGmiiigiUx3kKl6WZhXZgr6lMLQVSdz46NEiqrwjvSdu4qE4Xx-la52grhJHq"
        )
    api_identifier = input(
        "Enter your api url which will be used for configuring callbacks, web origins, etc:> "
    )
    mg = Auth0Manager(
        domain=domain,
        global_client_id=global_client_id,
        global_client_secret=global_client_secret,
        fqdn=api_identifier,
    )

    api = mg.initialize_api()
    app = mg.get_spa_client()
    logger.debug(json.dumps(api, indent=2))
    logger.debug(json.dumps(app, indent=2))


class Auth0Service:
    """Perform JSON Web Token (JWT) validation using PyJWT"""

    """Modified from Auth0 boilerplate"""

    def __init__(self, auth0_domain, auth0_audience):
        self.issuer_url = None
        self.audience = None
        self.algorithm = "RS256"
        self.jwks_uri = None
        self.issuer_url = f"https://{auth0_domain}/"
        self.jwks_uri = f"{self.issuer_url}.well-known/jwks.json"
        self.audience = auth0_audience

    def get_signing_key(self, token):
        try:
            jwks_client = jwt.PyJWKClient(self.jwks_uri)

            return jwks_client.get_signing_key_from_jwt(token).key
        except Exception as error:
            return UJSONResponse(
                content={
                    "error": "signing_key_unavailable",
                    "error_description": error.__str__(),
                    "message": "Unable to verify credentials",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def validate_jwt(self, token: str):
        try:
            jwt_signing_key = self.get_signing_key(token)

            payload = jwt.decode(
                token,
                jwt_signing_key,
                algorithms=self.algorithm,
                audience=self.audience,
                issuer=self.issuer_url,
            )
        except Exception as error:
            return UJSONResponse(
                content={
                    "error": "invalid_token",
                    "error_description": error.__str__(),
                    "message": "Bad credentials",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return payload

    def authorization_guard(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            # token = get_bearer_token_from_request()
            # validated_token = auth0_service.validate_jwt(token)

            # g.access_token = validated_token

            return function(*args, **kwargs)

        return decorator


auth0_service = Auth0Service()
