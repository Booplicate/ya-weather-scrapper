"""
Module implementing loging for fetching weather info
"""
# pylint: disable=broad-except


import abc
import atexit
from collections.abc import Iterator
import os
from typing import (
    Any,
    # Protocol,
    TypeVar
)


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.firefox.service import (
    Service as FirefoxService
)
from selenium.webdriver.firefox.options import (
    Options as FirefoxOptions
)


T = TypeVar("T", int, float, str)
V = TypeVar("V")

def _cast_if_not_none(value: str|None, type_: type[T], fallback: V|None = None) -> T|V|None:
    """
    Cast a value to a type if it's not None
    (supports ints, floats, strs)
    """
    if value is not None:
        try:
            return type_(value)

        except Exception:
            # TODO: logging
            return fallback

    return value

def _sanitize_float_sep(value: str) -> str:
    """
    Sanitizes float separator in the given string (replaces , with .)
    """
    return value.replace(",", ".")


class _WeatherRow():
    """
    Represents a weather row - weather during part of the day
    (like morning weather or evening weather)
    """
    def __init__(self):
        """
        Constructor
        """
        self._min_temp: int|None = None
        self._max_temp: int|None = None
        self._description: str|None = None
        self._pressure: int|None = None
        self._humidity: float|None = None
        self._wind: float|None = None

    def __str__(self):
        return (
            "<_WeatherRow("
            f"temp=({self.min_temp}, {self.max_temp}, {self.avr_temp}), "
            f"description='{self.description}', "
            f"pressure={self.pressure}, "
            f"humidity={self.humidity}, "
            f"wind={self.wind}"
            ")>"
        )

    __repr__ = __str__

    @property
    def avr_temp(self):
        """
        Dynamic prop returns average temp for this row
        """
        if self.min_temp is None or self.max_temp is None:
            return None
        return (self.min_temp + self.max_temp)//2

    @property
    def min_temp(self):
        return self._min_temp

    @min_temp.setter
    def min_temp(self, value: int|None):
        self._min_temp = value

    @property
    def max_temp(self):
        return self._max_temp

    @max_temp.setter
    def max_temp(self, value: int|None):
        self._max_temp = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str|None):
        self._description = value

    @property
    def pressure(self):
        return self._pressure

    @pressure.setter
    def pressure(self, value: int|None):
        self._pressure = value

    @property
    def humidity(self):
        return self._humidity

    @humidity.setter
    def humidity(self, value: float|None):
        self._humidity = value

    @property
    def wind(self):
        return self._wind

    @wind.setter
    def wind(self, value: float|None):
        self._wind = value

    def to_dict(self) -> dict[str, int|float|str|None]:
        """
        Converts this object into a dict
        """
        return {
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "avr_temp": self.avr_temp,
            "description": self.description,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "wind": self.wind
        }

class _WeatherBlock():
    """
    Represents a block of weather (morning, day, evening, night)
    """
    def __init__(self, weather_rows: list[_WeatherRow|None]|None = None):
        """
        Constructor
        """
        if weather_rows is None:
            weather_rows = [None]*4

        elif weather_rows and len(weather_rows) != 4:
            raise ValueError(f"_WeatherBlock expects exactly 4 rows, got: {len(weather_rows)}")

        self._rows: list[_WeatherRow|None] = weather_rows
        self._uv_index: int|None = None
        self._magnetic_field: str|None = None

    @property
    def uv_index(self):
        return self._uv_index

    @uv_index.setter
    def uv_index(self, value: int|None):
        self._uv_index = value

    @property
    def magnetic_field(self):
        return self._magnetic_field

    @magnetic_field.setter
    def magnetic_field(self, value: str|None):
        self._magnetic_field = value

    def __str__(self):
        return "<_WeatherBlock(\n    {},\n{}\n{}\n)>".format(
            ",\n    ".join(map(str, self._rows)),
            f"    uv_index={self.uv_index},",
            (
                f"    magnetic_field='{self.magnetic_field}'"
                if self.magnetic_field is not None
                else f"    magnetic_field={self.magnetic_field}"
            )
        )

    __repr__ = __str__

    def __len__(self):
        return len(self._rows)

    def _iter_rows_prop(self, prop: str, start: int|None = None, end: int|None = None):
        """
        Goes through all the rows and yield the required prop if it's not None,
        otherwise skip the row, the range can be specified
        via the start and end parameters
        """
        for row in self._rows[start:end]:
            if row is None:
                continue

            attr = getattr(row, prop)
            if attr is None:
                continue

            yield attr

    @property
    def avr_temp(self):
        """
        Calculates average temperature DURING DAYTIME
        """
        block_avr_temp = 0
        i = 0

        for row_avr_temp in self._iter_rows_prop("avr_temp", start=0, end=3):
            block_avr_temp += row_avr_temp
            i += 1

        if i != 0:
            # i can be 0 if all the blocks are None/missing avr temp
            return block_avr_temp // i
        return block_avr_temp

    @property
    def min_pressure(self) -> int|None:
        return min(self._iter_rows_prop("pressure"))

    @property
    def max_pressure(self) -> int|None:
        return max(self._iter_rows_prop("pressure"))

    def __getitem__(self, idx: int) -> _WeatherRow|None:
        return self._rows[idx]

    def __setitem__(self, idx: int, value: _WeatherRow|None):
        self._rows[idx] = value

    def __iter__(self) -> Iterator[_WeatherRow|None]:
        for row in self._rows:
            yield row

    def to_dict(self):
        """
        Converts this object into a dict
        """
        return {
            "weather": [r.to_dict() if r is not None else r for r in self],
            "avr_temp": self.avr_temp,
            "min_pressure": self.min_pressure,
            "max_pressure": self.max_pressure,
            "uv_index": self.uv_index,
            "magnetic_field": self.magnetic_field
        }

class WeatherReport():
    """
    Represent a weather report for multiple days
    """
    def __init__(self, weather_blocks: list[_WeatherBlock|None]|None = None, size: int = 7):
        """
        Constructor
        """
        if weather_blocks is None:
            weather_blocks = [None]*size

        elif weather_blocks and len(weather_blocks) != size:
            raise ValueError(f"WeatherReport expects exactly {size} blocks")

        self._blocks: list[_WeatherBlock|None] = weather_blocks

    def __str__(self):
        def fmt_block(block):
            if block is None:
                return f"{block}\n"
            return "".join(map(lambda s: f"    {s}\n", str(block).split("\n")))

        return "<WeatherReport(\n{})>".format(
            "".join(map(fmt_block, self._blocks))
        )

    __repr__ = __str__

    def __len__(self) -> int:
        return len(self._blocks)

    def __getitem__(self, idx: int) -> _WeatherBlock|None:
        # NOTE: doesn't support slices
        return self._blocks[idx]

    def __setitem__(self, idx: int, value: _WeatherBlock|None):
        # NOTE: doesn't support slices
        self._blocks[idx] = value

    def __iter__(self) -> Iterator[_WeatherBlock|None]:
        for block in self._blocks:
            yield block

    def to_dict(self):
        """
        Converts this object into a dict
        """
        return {
            "weather": [b.to_dict() if b is not None else b for b in self]
        }


class _DriverBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self) -> webdriver.remote.webdriver.WebDriver:
        ...

    @abc.abstractmethod
    def start(self) -> webdriver.remote.webdriver.WebDriver:
        ...

    @abc.abstractmethod
    def stop(self) -> webdriver.remote.webdriver.WebDriver:
        ...


class FFDriver(_DriverBase):
    """
    Firefox driver wrapper
    """
    # TODO: linux/mac version?
    DEF_DRIVER_PATH = "./yaws/drivers/geckodriver.exe"
    DEF_LOG_PATH = "./logs/geckodriver.log"

    def __init__(
        self,
        bin_path: str|None = None,
        driver_path: str|None = None,
        log_path: str|None = None
    ):
        """
        Constructor
        """
        if driver_path is None:
            driver_path = self.DEF_DRIVER_PATH

        options = FirefoxOptions()
        if bin_path:
            options.binary_location = bin_path
        options.headless = True

        if log_path is None:
            log_path = self.DEF_LOG_PATH

        try:
            log_path = log_path.replace("\\", "/")
            pure_path = log_path.rpartition("/")[0]
            os.makedirs(pure_path)
        except Exception:
            pass

        self.options = options
        self.service = FirefoxService(executable_path=driver_path, log_path=log_path)
        self.inner: webdriver.Firefox|None = None

        # Stop the engine at exit
        atexit.register(self.stop)

    def __call__(self):
        return self.inner

    def start(self):
        """
        Starts the driver
        """
        if self.inner is None:
            self.inner = webdriver.Firefox(service=self.service, options=self.options)

    def stop(self):
        """
        Stops the driver
        """
        if self.inner is not None:
            self.inner.quit()
            self.inner = None


class SeleniumScrapper():
    """
    Selenium weather scrapper
    """
    def __init__(self, driver: _DriverBase):
        self.driver = driver

    def start(self):
        """
        Starts the scrapper
        """
        self.driver.start()

    def stop(self):
        """
        Stops the scrapper
        """
        self.driver.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def get_report_from_url(self, url: str) -> WeatherReport:
        """
        Scraps weather info from a url
        """
        self.start()
        self._open_page(url)
        wait = WebDriverWait(self.driver(), 5.0)
        try:
            wait.until(
                expected_conditions.presence_of_element_located(
                    # Should reuse the path from the other method
                    (By.XPATH, "//article[@class='card']")
                )
            )
        except Exception:
            # Return empty report
            return WeatherReport()

        articles = self._get_weather_articles()
        return self._parse_weather_articles(articles)

    def _open_page(self, url: str):
        """
        Opens a webpage
        """
        d = self.driver()
        if d is not None:
            d.get(url)

    def _get_element_by_xpath(self, root: WebElement, xpath: str) -> WebElement|None:
        """
        Returns first element from the given node using xpath
        """
        try:
            return root.find_element(By.XPATH, xpath)

        except Exception:
            return None

    def _get_elements_by_xpath(self, root: WebElement, xpath: str) -> list[WebElement]:
        """
        Returns elements from the given node using xpath
        """
        return root.find_elements(By.XPATH, xpath)

    def _get_element_by_class(self, root: WebElement, klass: str) -> WebElement|None:
        """
        Returns first element filtering using their class name
        """
        try:
            return root.find_element(By.CLASS_NAME, klass)

        except Exception:
            return None

    def _get_weather_articles(self):
        d = self.driver()
        if d is not None:
            try:
                return d.find_elements(By.XPATH, "//article[@class='card']")

            except Exception:
                # TODO: log
                pass

        return []

    def _parse_weather_articles(self, articles: list[WebElement]) -> WeatherReport:
        report = WeatherReport()
        for i, article in enumerate(articles):
            table = self._get_element_by_xpath(article, "./div[2]/table")
            if table:
                wb = self._parse_weather_table(table)

                fields = self._get_element_by_xpath(article, "./div[2]/dl")
                if fields:
                    self._parse_footer_fields(fields, wb)

                report[i] = wb

            else:
                # TODO: log
                pass

            if i >= len(report)-1:
                break

        return report

    def _parse_weather_table(self, table: WebElement) -> _WeatherBlock:
        wb = _WeatherBlock()
        for i, row in enumerate(table.find_elements(By.CLASS_NAME, "weather-table__row")):
            wr = self._parse_weather_row(row)
            wb[i] = wr
            if i >= len(wb)-1:
                break

        return wb

    def _parse_weather_row(self, row: WebElement) -> _WeatherRow:
        wr = _WeatherRow()

        temps = row.find_elements(By.CLASS_NAME, "temp__value")
        if len(temps) == 3:
            wr.min_temp = self._parse_weather_temp(temps[0])
            wr.max_temp = self._parse_weather_temp(temps[1])

        elif len(temps) == 2:
            wr.min_temp = wr.max_temp = self._parse_weather_temp(temps[0])

        description = self._get_element_by_class(row, "weather-table__body-cell_type_condition")
        if description:
            wr.description = self._parse_weather_description(description)

        pressure = self._get_element_by_class(row, "weather-table__body-cell_type_air-pressure")
        if pressure:
            wr.pressure = self._parse_weather_pressure(pressure)

        humidity = self._get_element_by_class(row, "weather-table__body-cell_type_humidity")
        if humidity:
            wr.humidity = self._parse_weather_humidity(humidity)

        wind = self._get_element_by_class(row, "wind-speed")
        if wind:
            wr.wind = self._parse_weather_wind(wind)

        return wr

    def _parse_weather_temp(self, temp: WebElement) -> int|None:
        # Replace unicode '-' with the proper '-'
        rv = temp.text.replace("−", "-")
        return _cast_if_not_none(rv, int)

    def _parse_weather_description(self, description: WebElement) -> str:
        return description.text

    def _parse_weather_pressure(self, pressure: WebElement) -> int|None:
        return _cast_if_not_none(pressure.text, int)

    def _parse_weather_humidity(self, humidity: WebElement) -> float|None:
        rv = _cast_if_not_none(humidity.text.replace("%", ""), float)
        if rv is not None and rv > 1.0:
            rv /= 100.0
        return rv

    def _parse_weather_wind(self, wind: WebElement) -> float|None:
        return _cast_if_not_none(_sanitize_float_sep(wind.text), float)

    def _parse_footer_fields(self, fields: WebElement, wb: _WeatherBlock):
        footer_elements = self._get_elements_by_xpath(
            fields,
            "./dd[@class='forecast-fields__value']"
        )
        if footer_elements:
            uv_index = footer_elements[0]
            if uv_index:
                wb.uv_index = self._parse_footer_fields_uv_index(uv_index)

            if len(footer_elements) > 1:
                # Access last since there can be another element in the middle - water temp
                magnetic_field = footer_elements[-1]
                if magnetic_field:
                    wb.magnetic_field = self._parse_footer_fields_magnetic_field(magnetic_field)

    def _parse_footer_fields_uv_index(self, uv_index: WebElement) -> int|None:
        rv = uv_index.text
        # Hack in case we got only 1 field: water temp
        if rv.endswith("C"):
            return None
        return _cast_if_not_none(rv.split(",")[0], int)

    def _parse_footer_fields_magnetic_field(self, magnetic_field: WebElement) -> str|None:
        rv = magnetic_field.text
        # Hack in case we got only 2 fields: uv and water temp, but no magnetic field
        if rv.endswith("C"):
            return None
        return rv
