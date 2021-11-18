import requests
from requests.exceptions import HTTPError
from yarl import URL
import time

# HTTP verbs to be used as non string literals
DELETE = "DELETE"
GET = "GET"
POST = "POST"
PUT = "PUT"

class DiscourseClient:
    def __init__(self, host, api_username, api_key, timeout=None):
        self.host = host
        self.api_username = api_username
        self.api_key = api_key
        self.timeout = timeout

    def user_by_id(self, user_id):
        return self._get(f"admin/users/{user_id}.json")

    def group(self, group_name):
        return self._get(f"/groups/{group_name}.json")

    def group_owners(self, group_name):
        group = self._get(f"/groups/{group_name}/members.json")
        return group["owners"]

    def add_group_owner(self, groupid, username):
        return self._put(f"/admin/groups/{groupid}/owners.json", usernames=username)

    def group_members(self, group_name):
        group = self._get(f"/groups/{group_name}/members.json")
        return group["owners"]

    def add_group_member(self, groupid, username):
        return self._put(f"/admin/groups/{groupid}/members.json", usernames=username)

    def add_user_to_group(self, groupid, userid):
        return self._post(f"/admin/users/{userid}/groups", group_id=groupid)

    def _get(self, path, override_request_kwargs=None, **kwargs):
        return self._request(GET, path, params=kwargs, override_request_kwargs=override_request_kwargs)

    def _put(self, path, json=False, override_request_kwargs=None, **kwargs):
        if not json:
            return self._request(PUT, path, data=kwargs, override_request_kwargs=override_request_kwargs)
        else:
            return self._request(PUT, path, json=kwargs, override_request_kwargs=override_request_kwargs)

    def _post(self, path, files=None, json=False, override_request_kwargs=None, **kwargs):
        if not json:
            return self._request(POST, path, files=files, data=kwargs, override_request_kwargs=override_request_kwargs)
        else:
            return self._request(POST, path, files=files, json=kwargs, override_request_kwargs=override_request_kwargs)
    
    def _request(self, verb, path, params=None, files=None, data=None, json=None, override_request_kwargs=None):
        url = URL(self.host).with_path(path)

        print(url)

        headers = {
            "Accept": "application/json; charset=utf-8",
            "Api-Key": self.api_key,
            "Api-Username": self.api_username,
        }

        if override_request_kwargs is None:
            override_request_kwargs = {}

        retry_count = 5
        retry_backoff = 1

        while retry_count > 0:
            request_kwargs = dict(
                allow_redirects=False,
                params=params,
                files=files,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )

            request_kwargs.update(override_request_kwargs)

            response = requests.request(verb, url, **request_kwargs)

            if response.ok:
                break

            try:
                msg = u",".join(response.json()["errors"])
            except (ValueError, TypeError, KeyError):
                if response.reason:
                    msg = response.reason
                else:
                    msg = f"{response.status_code}: {response.text}"

            if 429 == response.status_code:
                rj = response.json()
                wait_delay = (
                    retry_backoff + rj["extras"]["wait_seconds"]
                )  # how long to back off for.

                if retry_count > 1:
                    time.sleep(wait_delay)
                retry_count -= 1
                continue

            raise HTTPError(msg, response=response)

        if retry_count == 0:
            raise HTTPError("Reached max retries", response=response)

        if response.status_code == 302:
            raise HTTPError("Unexpected redirect", response=response)

        json_content = "application/json; charset=utf-8"
        content_type = response.headers["content-type"]
        if content_type != json_content:
            # some calls return empty html documents
            if not response.content.strip():
                return None

            raise HTTPError(
                f'Invalid Response, expecting "{json_content}" got "{content_type}"',
                response=response,
            )

        try:
            decoded = response.json()
        except ValueError:
            raise HTTPError("failed to decode response", response=response)

        # Checking "errors" length because
        # data-explorer (e.g. POST /admin/plugins/explorer/queries/{}/run)
        # sends an empty errors array
        if "errors" in decoded and len(decoded["errors"]) > 0:
            message = decoded.get("message")
            if not message:
                message = u",".join(decoded["errors"])
            raise HTTPError(message, response=response)

        return decoded
