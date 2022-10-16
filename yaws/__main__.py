"""
Program entry point
"""


import argparse
import os
import platform

from . import (
    scrapper,
    export,
    urls,
    sql_backend,
    city_lookup
)


def init():
    """
    Convenient method to init all sub modules
    """
    city_lookup.init()
    sql_backend.init()

def main():
    """
    Program entry point
    """
    parser = argparse.ArgumentParser(prog="yaws", description="YAndex Weather Scrapper")
    parser.add_argument("city", help="the city to check the weather in")
    parser.add_argument(
        "-b",
        "--browser",
        default=None,
        help="path to the browser to use for scrapping (currently supported only Firefox)"
    )
    parser.add_argument("-d", "--driver", default=None, help="path to the browser driver")

    args = parser.parse_args()

    city_name = args.city
    browser_bin = args.browser
    driver = args.driver
    dump_path = os.getcwd()#"./"

    # We launched successfully, let's init
    init()

    # Now process user input
    city_data = city_lookup.get_city_data(city_name)

    if not city_data:
        print(f"Unknown city '{city_name}'")
        sql_backend.add_new_result_entry(city_name, False)
        return

    elif len(city_data) > 1:
        print("Multiple cities found, select one")
        while True:
            for i, data in enumerate(city_data):
                print(f"{i}: {data.name}, {data.region} ({data.district})")

            try:
                choice = int(input())
                city = city_data[choice]

            except (ValueError, IndexError):
                print("Invalid id")

            else:
                break

    else:
        city = city_data[0]

    print(f"Working with {city.name}, {city.region} ({city.district})")

    weather_url = urls.build_url_ya_pogoda(*city.coords)
    print("Loading...")
    driver = scrapper.FFDriver(browser_bin, driver)# pylint: disable=abstract-class-instantiated
    with scrapper.SeleniumScrapper(driver) as scrp:
        print("Fetching weather...")
        try:
            report = scrp.get_report_from_url(weather_url)

        except:# Catch the most generic exc
            # In case we crashed somehow, we mark it as a failure
            sql_backend.add_new_result_entry(city_name, False)
            raise

    print("Dumping...")

    try:
        file = export.to_excel(report, dump_path)

    except Exception as e:
        print(f"Failed to dump weather report: {e}")

    else:
        if platform.system() == "Windows":
            print("Done")
            os.startfile(file)

        else:
            print(f"Done, check '{file}'")

    # If we're here, we were able to fetch the weather
    sql_backend.add_new_result_entry(city_name, True)

if __name__ == "__main__":
    main()
