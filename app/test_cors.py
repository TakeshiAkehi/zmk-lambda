from fastapi import status
from fastapi.testclient import TestClient
from main import app


def test_cors_req(url):
    client = TestClient(app)
    print(f"request from %s" % url)
    headers = {"Origin": url, "Access-Control-Request-Method": "GET"}
    response = client.options("/", headers=headers)
    if response.status_code == status.HTTP_200_OK:
        assert response.headers["access-control-allow-origin"] == url
        print("Request allowed")
    elif status.HTTP_400_BAD_REQUEST == response.status_code:
        assert "access-control-allow-origin" not in response.headers
        print("Request not allowed")
    else:
        assert False

    return response


def test_disallowed_cors(client):
    print(f"request from %s (excepted diallowed)" % url)
    headers = {"Origin": url, "Access-Control-Request-Method": "GET"}
    response = client.options("/", headers=headers)


if __name__ == "__main__":
    # allow
    test_cors_req(url="http://test.origin.com")
