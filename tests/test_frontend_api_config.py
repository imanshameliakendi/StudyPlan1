from unittest.mock import patch

from frontend.api_config import LOCAL_BACKEND_URL, get_backend_url


def test_keeps_compose_service_url():
    with patch.dict("os.environ", {"BACKEND_BASE_URL": "http://backend:8000"}):
        assert get_backend_url() == "http://backend:8000"


def test_keeps_explicit_non_compose_backend_url():
    with patch.dict("os.environ", {"BACKEND_BASE_URL": "http://127.0.0.1:9000"}):
        assert get_backend_url() == "http://127.0.0.1:9000"


def test_uses_local_backend_by_default():
    with patch.dict("os.environ", {}, clear=True):
        assert get_backend_url() == LOCAL_BACKEND_URL
