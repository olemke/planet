#!/usr/bin/env python
# %%

import json
import sys
from multiprocessing import Pool

import planet_download as planet

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json")
        exit(1)

    with open(sys.argv[1], "r") as f:
        items = json.load(f)

    # # extract image IDs only
    image_ids = [r["id"] for r in items["results"]]

    args = [(id, items["config"]) for id in image_ids]
    with Pool(processes=3) as pool:
        pool.starmap(planet.download_image, args)
