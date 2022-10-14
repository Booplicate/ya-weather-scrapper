"""
Module for city lookup backend
"""

from __future__ import annotations

import csv
from collections import defaultdict


CITY_DB_PATH = "./city_coords.csv"



class CityData():
    """
    Class to represend information about a city
    """
    CITIES_MAP: defaultdict[str, list[CityData]] = defaultdict(list)

    def __init__(self, name: str, region: str, district: str, coords: tuple[float, float]):
        """
        Constructor
        """
        # NOTE: We're restricted to ONLY work with cities
        # can't use regions to distinguish dupes
        self.name = name
        self.region = region
        self.district = district
        self.coords = coords

    def __str__(self):
        return f"CityData('{self.name}', '{self.region}', '{self.district}', {self.coords})"

    __repr__ = __str__

    @classmethod
    def register_city(cls, *args, **kwargs):
        """
        Registers a new city
        """
        city = CityData(*args, **kwargs)
        key = city.name.replace(" ", "").lower()
        cls.CITIES_MAP[key].append(city)

    @classmethod
    def get_by_name(cls, name: str) -> list[CityData]:
        """
        Returns data for the cities with the given name
        """
        return cls.CITIES_MAP.get(name.lower(), [])


def _sanitize_coord(coord: str) -> float:
    return float(coord.replace(",", "."))

def init():
    """
    Inits city data from the csv db, must be called first
    """
    with open(CITY_DB_PATH, encoding="utf-8", newline="") as city_db:
        csv_reader = csv.reader(city_db, delimiter=";", strict=True)
        next(csv_reader)# skip csv structure line
        for data in csv_reader:
            name, region, district, lat, lon = data
            coords = (_sanitize_coord(lat), _sanitize_coord(lon))
            CityData.register_city(name, region, district, coords)

def get_city_data(name: str) -> list[CityData]:
    """
    Returns information about the cities with the given name
    """
    return CityData.get_by_name(name)
