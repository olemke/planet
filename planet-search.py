#!/usr/bin/env python
# %%

import json
import sys

import planet_download as planet

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} CONFIG.json")
    exit(1)

with open(sys.argv[1], "r") as f:
    config = json.load(f)

items = planet.build_filelist(config)

n_images = len(items)
print(f"{n_images} images selected")

with open(config["name"] + "-results.json", "w") as f:
    json.dump({"config": config, "results": items}, f)
