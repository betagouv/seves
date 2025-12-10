from functools import wraps

import os
import requests
from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import smart_str
from josepy.jws import JWS, Header
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import import_from_settings
from requests.auth import HTTPBasicAuth


_bundle_file_path = "bundle.pem"


def patch_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not os.environ.get("PEM_FILE"):
            return func(*args, **kwargs)
        if not os.path.exists(_bundle_file_path):
            pem_content = os.environ.get("PEM_FILE") or ""
            with open(_bundle_file_path, "w") as f:
                f.write(pem_content)
        kwargs["verify"] = _bundle_file_path
        return func(*args, **kwargs)

    return wrapper


class CustomOIDCBackend(OIDCAuthenticationBackend):
    def get_token(self, payload):
        """Return token object as a dictionary."""

        auth = None
        if self.get_settings("OIDC_TOKEN_USE_BASIC_AUTH", False):
            # When Basic auth is defined, create the Auth Header and remove secret from payload.
            user = payload.get("client_id")
            pw = payload.get("client_secret")

            auth = HTTPBasicAuth(user, pw)
            del payload["client_secret"]
        patched_post = patch_request(requests.post)
        response = patched_post(
            self.OIDC_OP_TOKEN_ENDPOINT,
            data=payload,
            auth=auth,
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        self.raise_token_response_error(response)
        return response.json()

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details dictionary. The id_token and payload are not used in
        the default implementation, but may be used when overriding this method"""
        patched_get = patch_request(requests.get)

        user_response = patched_get(
            self.OIDC_OP_USER_ENDPOINT,
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        user_response.raise_for_status()
        return user_response.json()

    def retrieve_matching_jwk(self, token):
        """Get the signing key by exploring the JWKS endpoint of the OP."""
        patched_get = patch_request(requests.get)
        response_jwks = patched_get(
            self.OIDC_OP_JWKS_ENDPOINT,
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        response_jwks.raise_for_status()
        jwks = response_jwks.json()

        # Compute the current header from the given token to find a match
        jws = JWS.from_compact(token)
        json_header = jws.signature.protected
        header = Header.json_loads(json_header)

        key = None
        for jwk in jwks["keys"]:
            if import_from_settings("OIDC_VERIFY_KID", True) and jwk["kid"] != smart_str(header.kid):
                continue
            if "alg" in jwk and jwk["alg"] != smart_str(header.alg):
                continue
            key = jwk
        if key is None:
            raise SuspiciousOperation("Could not find a valid JWKS.")
        return key

    def get_user(self, user_id):
        """Return a user based on the id."""
        try:
            return (
                self.UserModel.objects.filter(pk=user_id)
                .select_related("agent", "agent__structure")
                .prefetch_related("groups")
                .first()
            )
        except self.UserModel.DoesNotExist:
            return None
