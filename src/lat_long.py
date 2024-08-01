from functools import cache
import json
import math
import re

import urllib
import urllib.parse

from src.requests import get
from src.config import GEOAPIFY_API_KEY


def extract_plz(data: str) -> int | None:
    """Extract the postal code from the data."""
    res = re.search(r'\d{5}', data)
    if res is None:
        return None
    return int(res.group())


@cache
def plz_to_lat_long(plz: int) -> tuple[float, float]:
    """Convert the postal code to latitude and longitude."""
    # load the data/plz_geocoord.csv file
    # File is from: https://github.com/WZBSocialScienceCenter/plz_geocoord
    with open('data/plz_geocoord.csv', 'r') as file:
        lines = file.readlines()[1:]

    # find the line with the postal code
    for line in lines:
        line_plz, lat, long = line.split(',')
        if int(line_plz) == plz:
            return float(lat), float(long)

    print(f'Postal code not found: {plz}')
    return 0, 0  # return a default value which is far away from any location, so that the offer is not considered


def distance(lat_lng1: tuple[float, float], lat_lng2: tuple[float, float]) -> float:
    """Calculate the distance between two points in kilometers."""
    lat1, lng1 = lat_lng1
    lat2, lng2 = lat_lng2
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlng / 2) * math.sin(dlng / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


async def query_api_for_lat_lon(location: str) -> tuple[float, float]:
    """Query an API to get the latitude and longitude of the location."""
    url_encoded_parameters = urllib.parse.urlencode(
        {'text': location, 'apiKey': GEOAPIFY_API_KEY, 'filter': 'countrycode:de'}
    )
    response = await get(f'https://api.geoapify.com/v1/geocode/search?{url_encoded_parameters}')

    data = json.loads(response)
    coords = data['features'][0]['properties']
    return coords['lat'], coords['lon']
