import time
import json
import requests
from typing import Dict, Any, Optional

class JuiceShopApiClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: Optional[str] = None

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        start_time = time.time()
        res = self.session.request(method, url, **kwargs)
        duration_ms = int((time.time() - start_time) * 1000)

        try:
            import allure
            endpoint_path = url.replace(self.base_url, "")
            step_name = f"[API] {method.upper()} {endpoint_path} -> HTTP {res.status_code} ({duration_ms} ms)"
            with allure.step(step_name):
                # Формирование cURL команды для мгновенного ручного воспроизведения
                curl_cmd = [f"curl -X {method.upper()} '{url}'"]
                headers = {**self.session.headers, **kwargs.get("headers", {})}
                for k, v in headers.items():
                    curl_cmd.append(f"  -H '{k}: {v}'")
                if "json" in kwargs:
                    curl_cmd.append(f"  -d '{json.dumps(kwargs['json'])}'")
                allure.attach(
                    "\n".join(curl_cmd),
                    name=f"cURL: {method.upper()} {endpoint_path}",
                    attachment_type=allure.attachment_type.TEXT
                )

                # Прикрепление тела ответа с подсветкой синтаксиса
                if res.text:
                    content_type = res.headers.get("content-type", "").lower()
                    is_json = "json" in content_type
                    allure.attach(
                        res.text[:4000],
                        name=f"Response Body [{res.status_code}]",
                        attachment_type=allure.attachment_type.JSON if is_json else allure.attachment_type.TEXT
                    )
        except Exception:
            pass

        return res

    def get_connection_status(self) -> requests.Response:
        return self._request("GET", f"{self.base_url}/rest/admin/application-version")

    def set_bearer_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self.token = None
        self.session.headers.pop("Authorization", None)

    def set_security_answer(self, user_id: int, question_id: int = 1, answer: str = "JuiceQA") -> requests.Response:
        url = f"{self.base_url}/api/SecurityAnswers/"
        payload = {
            "UserId": user_id,
            "answer": answer,
            "SecurityQuestionId": question_id
        }
        return self._request("POST", url, json=payload)

    def register(self, email: str, password: str, question_id: int = 1, answer: str = "JuiceQA", link_security_answer: bool = True) -> requests.Response:
        url = f"{self.base_url}/api/Users/"
        payload = {
            "email": email,
            "password": password,
            "securityQuestion": {
                "id": question_id,
                "question": "Your eldest siblings middle name?",
                "createdAt": "2021-01-01T00:00:00.000Z",
                "updatedAt": "2021-01-01T00:00:00.000Z"
            },
            "SecurityQuestionId": question_id,
            "securityAnswer": answer
        }
        res = self._request("POST", url, json=payload)
        if link_security_answer and res.status_code == 201:
            try:
                user_id = res.json().get("data", {}).get("id")
                if user_id:
                    self.set_security_answer(user_id, question_id, answer)
            except Exception:
                pass
        return res

    def login(self, email: str, password: str) -> requests.Response:
        url = f"{self.base_url}/rest/user/login"
        payload = {"email": email, "password": password}
        res = self._request("POST", url, json=payload)
        if res.status_code == 200:
            data = res.json()
            token = data.get("authentication", {}).get("token")
            if token:
                self.set_bearer_token(token)
        return res

    def change_password(self, current_password: str, new_password: str, repeat_password: str, token: Optional[str] = None) -> requests.Response:
        url = f"{self.base_url}/rest/user/change-password"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params = {
            "current": current_password,
            "new": new_password,
            "repeat": repeat_password
        }
        return self._request("GET", url, params=params, headers=headers)

    def reset_password(self, email: str, answer: str, new_password: str, repeat_password: str) -> requests.Response:
        url = f"{self.base_url}/rest/user/reset-password"
        payload = {
            "email": email,
            "answer": answer,
            "new": new_password,
            "repeat": repeat_password
        }
        return self._request("POST", url, json=payload)

    def create_address(self, country: str, full_name: str, mobile: str, zip_code: str, street_address: str, city: str, token: Optional[str] = None) -> requests.Response:
        url = f"{self.base_url}/api/Addresss/"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {
            "country": country,
            "fullName": full_name,
            "mobileNum": mobile,
            "zipCode": zip_code,
            "streetAddress": street_address,
            "city": city
        }
        return self._request("POST", url, json=payload, headers=headers)

    def upload_avatar(self, file_content: bytes, filename: str, mime_type: str = "image/png", token: Optional[str] = None) -> requests.Response:
        url = f"{self.base_url}/profile/image/file"
        active_token = token or self.token
        headers = {}
        cookies = {}
        if active_token:
            headers["Authorization"] = f"Bearer {active_token}"
            cookies["token"] = active_token
        files = {
            "file": (filename, file_content, mime_type)
        }
        return self._request("POST", url, files=files, headers=headers, cookies=cookies, allow_redirects=False)

    def get_user_profile(self, token: Optional[str] = None) -> requests.Response:
        url = f"{self.base_url}/rest/user/whoami"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self._request("GET", url, headers=headers)

    def search_products(self, query: str = "") -> requests.Response:
        url = f"{self.base_url}/rest/products/search"
        params = {"q": query} if query is not None else {}
        return self._request("GET", url, params=params)

    def get_product(self, product_id: int) -> requests.Response:
        url = f"{self.base_url}/api/Products/{product_id}"
        return self._request("GET", url)
