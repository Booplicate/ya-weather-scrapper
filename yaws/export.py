"""
Module implements logic for exporting data
"""


# import json
import datetime
import time
import os
from typing import (
    TypeVar
)

import pandas

from .scrapper import WeatherReport, _WeatherBlock


DAY_W_REPORT_ROW_NAMES = ("Morning", "Day", "Evening", "Night")
DAY_W_REPORT_COLUMN_NAMES = ("Temperature", "Pressure", "Humidity", "Description")
FALLBACK_VALUE = "Unknown"
FINAL_W_REPORT_COLUMN_NAMES = ("Date", "Magnetic Field", "Average Temperature", "Warnings")

SUMMARY_SHEET = "Summary"

WARNING_PRESSURE_RAISE = "Ожидается резкое увеличение атмосферного давления"
WARNING_PRESSURE_DROP = "Ожидается резкое падение атмосферного давления"
WARNING_PRESSURE_UNSTABLE = "Ожидается резкие перепады атмосферного давления"


T = TypeVar("T")
S = TypeVar("S")

def _replace_none(value: T, fallback: S) -> T|S:
    """
    Replaces the provided value with the fallback value if it's None,
    otherwise returns the value
    """
    if value is None:
        return fallback
    return value

def _select_warning(weather_block: _WeatherBlock) -> str:
    """
    Selects an appropriate warning based on some conditions (like pressure change)
    """
    if weather_block.max_pressure is not None and weather_block.min_pressure is not None:
        pressure_diff = weather_block.max_pressure - weather_block.min_pressure
        if pressure_diff >= 5:
            pressure_data = pandas.Series(i.pressure for i in weather_block if i is not None)
            diff = pressure_data.diff()[1:].mean()
            if diff > 0.5:
                return WARNING_PRESSURE_RAISE

            elif diff < -0.5:
                return WARNING_PRESSURE_DROP

            else:
                return WARNING_PRESSURE_UNSTABLE

    return ""

def to_excel(report: WeatherReport, path: str, today: datetime.date|None = None) -> str:
    """
    Exports WeatherReport to excel
    """
    if today is None:
        today = datetime.date.today()

    writter_path = os.path.join(path, f"weather-dump-{time.time():.0f}.xlsx")

    with pandas.ExcelWriter(writter_path) as writter:# pylint: disable=abstract-class-instantiated
        summary_report_df = pandas.DataFrame(
            [[None]*4]*len(report),
            columns=FINAL_W_REPORT_COLUMN_NAMES
        )

        for k, weather_block in enumerate(report):
            if not weather_block:
                continue

            date = today + datetime.timedelta(days=k)
            daily_report_df = pandas.DataFrame(
                index=DAY_W_REPORT_ROW_NAMES,
                columns=DAY_W_REPORT_COLUMN_NAMES
            )

            for i, weather_row in enumerate(weather_block):
                if not weather_row:
                    continue

                daily_report_df.iloc[i] = pandas.Series(
                    (
                        _replace_none(weather_row.avr_temp, fallback=FALLBACK_VALUE),
                        _replace_none(weather_row.pressure, fallback=FALLBACK_VALUE),
                        _replace_none(weather_row.humidity, fallback=FALLBACK_VALUE),
                        _replace_none(weather_row.description, fallback=FALLBACK_VALUE)
                    )
                )
            # Write the daily report
            daily_report_df.to_excel(writter, sheet_name=f"{date.isoformat()}")
            # Fill the summary frame at the same time
            summary_report_df.iloc[k] = pandas.Series(
                (
                    date,
                    _replace_none(weather_block.magnetic_field, fallback=FALLBACK_VALUE),
                    _replace_none(weather_block.avr_temp, fallback=FALLBACK_VALUE),
                    _select_warning(weather_block),
                )
            )
        # Write the summary
        summary_report_df.to_excel(writter, sheet_name=SUMMARY_SHEET, index=False)

    return writter_path
