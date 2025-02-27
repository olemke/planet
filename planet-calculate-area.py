#!/usr/bin/env python
# %%

import json
import sys

import planet_download as planet

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json")
        exit(1)

    resultsfile = sys.argv[1]
    with open(resultsfile, "r") as f:
        items = json.load(f)

    geod_area_km2 = planet.calc_total_area(items) / 1000 / 1000

    print(f"{len(items['results'])} images")
    print(f"Geodesic area: {geod_area_km2:.3f} km^2")
