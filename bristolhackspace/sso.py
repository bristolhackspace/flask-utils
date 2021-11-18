from flask import redirect, request, session
import secrets
from urllib.parse import urlencode, parse_qs
import base64
import hmac
import hashlib
from yarl import URL
from functools import wraps


class BaseDiscourseSSO:
    def __init__(self, key, provider_url):
        self._key = key
        self._provider_url = provider_url

    def on_login_fail(self):
        return "Login failed"

    def on_new_login(self, args):
        member_id = int(args["external_id"][0])
        session["member_id"] = member_id
        session["username"] = args["username"][0]

    def load_login_data(self):
        pass

    def is_logged_in(self):
        return "member_id" in session

    def requires_login(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = None
            if not self.is_logged_in():
                if "sso" in request.args and "sig" in request.args:
                    response = self._decode_sso_login(
                        request.args["sso"], request.args["sig"]
                    )
                else:
                    response = self._redirect_to_sso_provider()

            if response is not None:
                return response
            else:
                self.load_login_data()
                return func(*args, **kwargs)

        return wrapper

    def _compute_sso_hash(self, sso):
        return hmac.new(self._key, sso, hashlib.sha256).hexdigest()

    def _decode_sso_login(self, sso, sig):
        if sig != self._compute_sso_hash(sso.encode("utf-8")):
            return self.on_login_fail()

        qs = base64.b64decode(sso).decode("utf-8")
        args = parse_qs(qs)
        try:
            session_nonce = session.pop("nonce")
            if args["nonce"][0] != session_nonce:
                return self.on_login_fail()

            self.on_new_login(args)

        except KeyError as ex:
            return self.on_login_fail()

    def _redirect_to_sso_provider(self):
        nonce = secrets.token_urlsafe()
        session["nonce"] = nonce
        qs = {"nonce": nonce, "return_sso_url": request.base_url}
        query_string = urlencode(qs)
        encoded_str = base64.b64encode(query_string.encode("utf-8"))

        remote_url = URL(self._provider_url).with_path("/session/sso_provider")
        remote_url = remote_url.with_query(
            {
                "sso": encoded_str.decode("utf-8"),
                "sig": self._compute_sso_hash(encoded_str),
            }
        )

        return redirect(str(remote_url), 302)
