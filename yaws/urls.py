"""
Module with url and builders to access extenral resources
"""


from urllib.parse import urlunparse
from typing import Literal


URL_SCHEME = Literal["http", "https"]

BASE = "{{scheme}}://{netloc}/{path}/{query}"

_YA_NETLOC = "yandex.ru"
_YA_PATH = "pogoda/details"
_YA_PARAMS = ""
_YA_QUERY = "lat={lat}&lon={lon}&via=ms"


def _build_url(scheme: URL_SCHEME, netloc: str, path: str, params: str, query: str, lat: float, lon: float) -> str:
    """
    Builds a url to access a service
    """
    url = urlunparse((scheme, netloc, path, params, query, ""))
    return url.format(
        lat=lat,
        lon=lon
    )


def build_url_ya_pogoda(lat: float, lon: float, scheme: URL_SCHEME = "https") -> str:
    """
    Builds a url to access YA_POGODA
    """
    return _build_url(
        scheme,
        _YA_NETLOC,
        _YA_PATH,
        _YA_PARAMS,
        _YA_QUERY,
        lat,
        lon,
    )
