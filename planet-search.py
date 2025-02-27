#!/usr/bin/env python
# %%

import json
import sys

import planet_download as planet

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} CONFIG.json")
    exit(1)

configfile = sys.argv[1]
with open(configfile, "r") as f:
    config = json.load(f)
name = planet.get_config_basename(configfile)

items = planet.build_filelist(config)

n_images = len(items)
print(f"{n_images} images selected")

with open(name + "-results.json", "w") as f:
    json.dump({"config": config, "results": items}, f)
