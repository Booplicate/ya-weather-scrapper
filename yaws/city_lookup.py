"""
Module for city lookup backend
"""

from __future__ import annotations

import csv
from collections import defaultdict


CITY_DB_PATH = "./yaws/city_coords.csv"



class CityData():
    """
    Class to represent information about a city
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

    @staticmethod
    def __name_to_key(name: str) -> str:
        """
        Converts a city name to a key to use in the inner map
        """
        return name.replace(" ", "").lower()

    @classmethod
    def register_city(cls, *args, **kwargs):
        """
        Registers a new city
        """
        city = CityData(*args, **kwargs)
        key = cls.__name_to_key(city.name)
        cls.CITIES_MAP[key].append(city)

    @classmethod
    def get_by_name(cls, name: str) -> list[CityData]:
        """
        Returns data for the cities with the given name
        """
        return cls.CITIES_MAP.get(cls.__name_to_key(name), [])


def _sanitize_coord(coord: str) -> float:
    return float(coord.replace(",", "."))

def init(db_path: str|None = None):
    """
    Inits city data from the csv db, must be called first
    """
    if db_path is None:
        db_path = CITY_DB_PATH

    with open(db_path, encoding="utf-8", newline="") as city_db:
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
