from drafter import *
from dataclasses import dataclass
from datetime import date, datetime
import requests
import csv
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

set_website_title("Historical Weather Records")
set_site_information(
    author="Holten Bosco",
    description="View the historical weather records for cities around Newark DE",
    sources="Data provided by Open-Meteo",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/holtenb-alt/historical-weather-records"]
)
hide_debug_information()
set_website_framed(False)

"""
The datetime library provides tools for working with dates and times

The imports csv and io help to create downloadable spreadsheets
CSV: a format that organizes info into rows and columns
"""

"""
Requests import and the URL below allows this program to communicate
with the Open-Meteo program. This site first requests the data, then
Open-Meteo processes the request and sends back the proper info.
"""
API_URL = "https://archive-api.open-meteo.com/v1/archive"

EARLIEST_DATE = "1980-01-01"
LATEST_DATE = "2026-11-01"


LOCATIONS = [
    ("Newark DE - 39.68, -75.75", 39.68, -75.75),
    ("Middletown DE - 39.75, -75.55", 39.75, -75.55),
    ("Wilmington DE - 39.45, -75.72", 39.45, -75.72),
    ("Dover DE - 39.16, -75.53", 39.16, -75.53),
    ("Philadelphia PA - 39.95, -75.17", 39.95, -75.17),
    ("Baltimore MD - 39.29, -76.61", 39.29, -76.61)
]

MONTHS = [
    ("01", "January"),
    ("02", "February"),
    ("03", "March"),
    ("04", "April"),
    ("05", "May"),
    ("06", "June"),
    ("07", "July"),
    ("08", "August"),
    ("09", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December")
]



@dataclass
class WeatherRecord:
    date: str
    temperature_high: float
    temperature_low: float
    temperature_average: float
    precipitation: float
    location: str


@dataclass
class State:
    selected_location: str
    selected_date: str
    selected_month_day: str
    selected_year: int
    weather_records: list
    search_type: str
    message: str



def find_location(location_name):
    """Find the coordinates associated with a location."""

    for location in LOCATIONS:
        if location[0] == location_name:
            return location

    return None


def fetch_weather(state, start_date, end_date,
                  calendar_month_day=None):
    """
    Retrieve daily weather information from Open-Meteo.

    Each API response is converted into WeatherRecord
    instances and stored in the State dataclass.

    calendar_month_day is optional. When supplied,
    only matching month/day records are retained.
    """

    location = find_location(state.selected_location)

    if location is None:
        state.message = "Please select a valid location."
        return

    latitude = location[1]
    longitude = location[2]

    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "temperature_2m_mean,"
            "precipitation_sum"
        ),
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
        "models": "era5"
    }

    state.weather_records = []
    state.message = ""
    """
    'try' attempts to execute the code in its body, and if an error occurs,
    'except' is used to execute alternative code.
    """
    try:
        response = requests.get(API_URL, params=parameters)

        response.raise_for_status()
        """
        The .json() converts the returned JSON data into Python data that
        this program can access.
        
        JSON organizes and transfers information between different programs
        """
        data = response.json()

        daily = data["daily"]

        dates = daily["time"]
        highs = daily["temperature_2m_max"]
        lows = daily["temperature_2m_min"]
        averages = daily["temperature_2m_mean"]
        precipitation = daily["precipitation_sum"]

        # Iterate through the daily API information.
        for i in range(len(dates)):

            current_date = dates[i]

            # Calendar searches only retain matching dates.
            if calendar_month_day is not None:

                current_month_day = current_date[5:10]

                if current_month_day != calendar_month_day:
                    continue

            # Ignore records with incomplete measurements.
            if (highs[i] is None or
                lows[i] is None or
                averages[i] is None or
                precipitation[i] is None):
                continue

            record = WeatherRecord(
                current_date,
                highs[i],
                lows[i],
                averages[i],
                precipitation[i],
                state.selected_location
            )

            state.weather_records.append(record)

        if len(state.weather_records) == 0:
            state.message = "No weather records were found."

        else:
            state.message = (
                "Successfully retrieved "
                + str(len(state.weather_records))
                + " weather records."
            )

    except Exception as error:
        state.message = (
            "Unable to retrieve weather information. "
            "Check your internet connection and API request. "
            + str(error)
        )


def calculate_statistics(records):
    """Calculate statistics from WeatherRecord instances."""

    if len(records) == 0:
        return None

    total_temperature = 0
    total_precipitation = 0

    highest_temperature = records[0]
    lowest_temperature = records[0]

    for record in records:

        total_temperature += record.temperature_average

        total_precipitation += record.precipitation

        if record.temperature_high > highest_temperature.temperature_high:
            highest_temperature = record

        if record.temperature_low < lowest_temperature.temperature_low:
            lowest_temperature = record

    average_temperature = total_temperature / len(records)

    return (
        average_temperature,
        total_precipitation,
        highest_temperature,
        lowest_temperature
    )


def create_csv(records):
    """
    Convert weather records into downloadable CSV text.
    
    io.StringIO() creates an in-memory location for text
    to be stored.
    
    csv.writer() creates a tool for writing CSV info.
    
    writer.writerow() adds a single row of info.
    
    output.getvalue() retrieves all of the generated text
    """

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Location",
        "Maximum Temperature (F)",
        "Minimum Temperature (F)",
        "Average Temperature (F)",
        "Precipitation (inches)"
    ])

    for record in records:
        writer.writerow([
            record.date,
            record.location,
            record.temperature_high,
            record.temperature_low,
            record.temperature_average,
            record.precipitation
        ])

    return output.getvalue()


def create_temperature_graph(records):
    """Create a graph of average daily temperatures."""

    dates = []
    temperatures = []

    for record in records:
        dates.append(record.date)
        temperatures.append(record.temperature_average)

    plt.figure(figsize=(10, 5))

    plt.plot(dates, temperatures, color="blue")

    plt.title("Historical Average Daily Temperature")

    plt.xlabel("Date")
    plt.ylabel("Temperature (Fahrenheit)")

    plt.xticks(rotation=45)

    plt.grid(True)

    plt.tight_layout()



@route
def index(state: State) -> Page:

    return Page(state, [

        Header("Historical Weather Explorer"),

        Text(
            "Explore historical temperature and "
            "precipitation records for selected locations."
        ),

        Header("What would you like to explore?", 2),

        Button("Select a Location", "locations"),

        Button("About This Project", "about"),

        HorizontalRule(),

        Text("Weather data provided by Open-Meteo.")

    ])



@route
def locations(state: State) -> Page:

    location_names = []

    for location in LOCATIONS:
        location_names.append(location[0])

    return Page(state, [

        Header("Select a Weather Location"),

        Text(
            "Choose a location to explore its "
            "historical weather information."
        ),

        SelectBox(
            "location_name",
            location_names,
            default_value=state.selected_location
        ),

        Button("Confirm Location", "choose_location"),

        Text(
            "Currently selected: "
            + state.selected_location
        ),

        HorizontalRule(),

        Header("Choose Your Search Type", 2),

        Text(
            "Select how you would like to explore "
            "historical weather records."
        ),

        Button(
            "Specific Date Search",
            "search"
        ),

        Button(
            "Calendar Day History",
            "calendar_history"
        ),

        Button(
            "Entire Year History",
            "year_history"
        ),

        HorizontalRule(),

        Button("Return Home", "index")

    ])



@route
def choose_location(state: State,
                    location_name: str) -> Page:

    if find_location(location_name) is None:

        state.message = "Invalid location selection."

    else:

        state.selected_location = location_name

        state.weather_records = []

        state.message = "Location successfully selected."

    return locations(state)



@route
def search(state: State) -> Page:

    return Page(state, [

        Header("Search a Specific Date"),

        Text(
            "Enter a date to find its historical "
            "temperature and precipitation."
        ),

        Text("Selected location: " + state.selected_location),

        Text("Enter a date in YYYY-MM-DD format:"),

        TextBox("date_text"),

        Button("Search Weather", "specific_date"),

        Button("Return Home", "index")

    ])


@route
def specific_date(state: State,
                  date_text: str) -> Page:

    try:
        """
        strptime() converts text into a Python date/time object
        %Y: The year, as four digits
        %m: The month, as two digits
        %d: The day, as two digits
        """
        requested_date = datetime.strptime(
            date_text, "%Y-%m-%d"
        ).date()
        """
        date.fromisoformat() converts the date as text
        into a date object
        
        Allows the program to compare date strings alphabetically
        """
        if requested_date < date.fromisoformat(EARLIEST_DATE):
            state.message = "Date is earlier than available data."

            return search(state)

        if requested_date > date.fromisoformat(LATEST_DATE):
            state.message = "Date is outside the available data range."

            return search(state)

        state.selected_date = date_text

        state.search_type = "Specific Date"

        fetch_weather(state, date_text, date_text)

        return specific_date_results(state)

    except ValueError:

        state.message = (
            "Invalid date. Please use YYYY-MM-DD."
        )

        return search(state)



@route
def calendar_history(state: State) -> Page:

    month_options = []

    for month in MONTHS:
        month_options.append(month[0])

    return Page(state, [

        Header("Calendar Day History"),

        Text(
            "Find historical weather records for "
            "the same month and day across multiple years."
        ),

        Text("Choose a month:"),

        SelectBox(
            "month",
            month_options,
            default_value="01"
        ),

        Text("Enter a day:"),

        TextBox("day"),

        Text("Starting year:"),

        TextBox("start_year"),

        Text("Ending year:"),

        TextBox("end_year"),
        
        HorizontalRule(),

        Button("Search Calendar History", "calendar_search"),

        Button("Return Home", "index")

    ])


@route
def calendar_search(state: State,
                    month: str,
                    day: str,
                    start_year: str,
                    end_year: str) -> Page:

    try:

        month_number = int(month)
        day_number = int(day)

        first_year = int(start_year)
        last_year = int(end_year)

        # Check that the month and day form a valid date.
        date(2000, month_number, day_number)

        if first_year < 1980 or last_year > 2026:
            state.message = "Years must be between 1980 and 2026."

            return calendar_history(state)

        if first_year > last_year:
            state.message = "Starting year must come before ending year."

            return calendar_history(state)

        state.selected_month_day = (
            month.zfill(2) + "-" + day.zfill(2)
        )

        state.selected_year = last_year

        state.search_type = "Calendar Day History"

        start_date = str(first_year) + "-01-01"

        end_date = min(
            str(last_year) + "-12-31",
            LATEST_DATE
        )

        fetch_weather(
            state,
            start_date,
            end_date,
            state.selected_month_day
        )

        return calendar_results(state)

    except ValueError:

        state.message = "Please enter a valid month, day, and year."

        return calendar_history(state)



@route
def year_history(state: State) -> Page:

    return Page(state, [

        Header("Explore an Entire Year"),

        Text(
            "View daily weather records and "
            "yearly temperature and precipitation statistics."
        ),

        Text("Enter a year between 1980 and 2026:"),

        TextBox("year_text"),

        Button("Search Year", "year_search"),

        Button("Return Home", "index")

    ])


@route
def year_search(state: State,
                year_text: str) -> Page:

    try:

        selected_year = int(year_text)

        if selected_year < 1980 or selected_year > 2026:

            state.message = "Please select a year from 1980 to 2026."

            return year_history(state)

        state.selected_year = selected_year

        state.search_type = "Yearly History"

        start_date = str(selected_year) + "-01-01"

        end_date = min(
            str(selected_year) + "-12-31",
            LATEST_DATE
        )

        fetch_weather(state, start_date, end_date)

        return yearly_results(state)

    except ValueError:

        state.message = "Please enter a valid numerical year."

        return year_history(state)


def create_year_graphs(records):
    plt.close("all")

    dates = []
    highs = []
    lows = []
    averages = []
    precipitation = []

    # Collect the information from every daily record
    for record in records:
        dates.append(record.date)
        highs.append(record.temperature_high)
        lows.append(record.temperature_low)
        averages.append(record.temperature_average)
        precipitation.append(record.precipitation)

    # Create one figure with two graphs
    plt.figure(figsize=(12, 9))

    # First graph: Temperature
    plt.subplot(2, 1, 1)

    plt.plot(dates, highs, label="Daily High")
    plt.plot(dates, lows, label="Daily Low")
    plt.plot(dates, averages, label="Daily Average")

    plt.title("Daily Temperatures Throughout the Year")
    plt.xlabel("Date")
    plt.ylabel("Temperature (F)")
    plt.legend()
    plt.gca().xaxis.set_major_locator(
        mdates.MonthLocator(bymonthday=1)
    )
    plt.xticks(rotation=30)

    # Second graph: Precipitation
    plt.subplot(2, 1, 2)

    plt.bar(dates, precipitation)

    plt.title("Daily Precipitation Throughout the Year")
    plt.xlabel("Date")
    plt.ylabel("Precipitation (inches)")
    plt.gca().xaxis.set_major_locator(
        mdates.MonthLocator(bymonthday=1)
    )
    plt.xticks(rotation=30)

    plt.tight_layout()
"""
plt.tight_layout() adjusts spacing between graph elements

plt.gca() gets the current graph's axes
.xaxis accesses the horizontal axis
MonthLocator() tells Matplotlib where to place date labels
"""

@route
def specific_date_results(state: State):
    if len(state.weather_records) == 0:
        return Page(state, [
            Header("Specific Date Results"),
            Text("No weather records were found for this date."),
            Button("Back to Date Search", "search")
        ])

    record = state.weather_records[0]

    return Page(state, [
        Header("Weather for " + record.date),
        Text("Location: " + state.selected_location),

        Header("Temperature"),
        Text("High: " + str(record.temperature_high) + " °F"),
        Text("Low: " + str(record.temperature_low) + " °F"),
        Text("Average: " + str(record.temperature_average) + " °F"),

        Header("Precipitation"),
        Text(str(record.precipitation) + " inches"),
        
        HorizontalRule(),
        
        Button("Search Another Date", "search"),
        Button("Choose Another Search", "locations")
    ])



@route
def calendar_results(state: State):
    if len(state.weather_records) == 0:
        return Page(state, [
            Header("Calendar Day Results"),
            Text("No records were found for this calendar day."),
            Button("Back to Calendar Search", "calendar_history")
        ])

    components = [
        Header("Calendar Day History"),
        Text("Location: " + state.selected_location),
        Text("Calendar Day: " + state.selected_month_day)
    ]

    for record in state.weather_records:
        components.append(Header(record.date))
        components.append(
            Text("High: " + str(record.temperature_high) + " °F")
        )
        components.append(
            Text("Low: " + str(record.temperature_low) + " °F")
        )
        components.append(
            Text("Average: " + str(record.temperature_average) + " °F")
        )
        components.append(
            Text("Precipitation: " + str(record.precipitation) + " inches")
        )

    components.append(Button("Search Another Calendar Day", "calendar_history"))
    components.append(Button("Choose Another Search", "locations"))

    return Page(state, components)


@route
def yearly_results(state: State):
    if len(state.weather_records) == 0:
        return Page(state, [
            Header("Yearly Weather Results"),
            Text("No weather records were found for this year."),
            Button("Back to Year Search", "year_history")
        ])

    # Create the graphs before displaying the page
    create_year_graphs(state.weather_records)

    return Page(state, [
        Header("Weather Results for " + str(state.selected_year)),

        Text("Location: " + state.selected_location),

        Header("Yearly Weather Graphs"),

        MatPlotLibPlot(),

        Button("Search Another Year", "year_history"),
        Button("Choose Another Search", "locations")
    ])


@route
def about(state: State) -> Page:

    return Page(state, [

        Header("About Historical Weather Explorer"),

        Text(
            "This website allows users to explore historical "
            "temperature and precipitation information."
        ),

        Header("Weather Data Source", 2),

        Text(
            "Historical weather information is retrieved "
            "from the Open-Meteo Historical Weather API."
        ),

        Text(
            "The application uses ERA5 historical reanalysis "
            "data and retrieves daily temperature and "
            "precipitation information."
        ),

        Header("Weather Measurements", 2),

        Text("Maximum temperature: Fahrenheit"),

        Text("Minimum temperature: Fahrenheit"),

        Text("Mean temperature: Fahrenheit"),

        Text("Total precipitation: Inches"),

        Header("Important Information", 2),

        Text(
            "These values are historical reanalysis estimates, "
            "not necessarily direct measurements from a "
            "weather station."
        ),

        Text(
            "Open-Meteo data may contain missing values "
            "or unavailable dates."
        ),

        Button("Return Home", "index")

    ])


start_server(

    State(
        LOCATIONS[0][0],
        "",
        "",
        2020,
        [],
        "",
        ""
    )

)

