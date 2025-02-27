#!/usr/bin/env python
# %%

import json
import sys

from pyproj import Geod
from shapely.geometry.polygon import Polygon

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json")
        exit(1)

    resultsfile = sys.argv[1]
    with open(resultsfile, "r") as f:
        items = json.load(f)

    locations = [Polygon(ts["geometry"]["coordinates"][0]) for ts in items["results"]]

    geod = Geod(ellps="WGS84")
    geod_area = sum(abs(geod.geometry_area_perimeter(loc)[0]) for loc in locations)

    print(f"{len(items['results'])} images")
    print(f"Geodesic area: {geod_area / 1000 / 1000:.3f} km^2")
