# [yaws](https://github.com/Booplicate/ya-weather-scrapper) - a weather scrapper


### Installing:
- install [Firefox](https://www.mozilla.org/en-US/firefox/all/#product-desktop-release)
- get the appropriate [Firefox driver](https://github.com/mozilla/geckodriver/releases/) for your OS
- - place the driver into `yaws/drivers`, or provide a path to it via the cli argument
- install Python `3.10.4`
- `cd` into `ya-weather-scrapper`
- create and enable a new virtual environment
- - `python -m venv ./venv`
- - `./venv/Scripts/activate`
- install Python dependencies
- - `pip install -r "./requirements.txt"`
- Deactivate venv when done
- - `deactivate`


### Usage:
To get help type:
- `python -m yaws -h`

Example of a valid command:
- `python -m yaws cityname`

In case firefox was installed in a non-standard directory, provide the path to it:
- `python -m yaws cityname --browser "C:/Program Files/Mozilla Firefox/firefox.exe"`

In case the driver was placed outside of the default directory, provide the path to it:
- `python -m yaws cityname --driver "C:/Program Files/Selenium Drivers/geckodriver.exe"`


### Stack:
- `Python 3.10.4`
- `selenium` (using Firefox backend)
- `pandas`
- `openpyxl`
- `sqlalchemy`
