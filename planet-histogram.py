#!/usr/bin/env python
# %%
import json
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

import planet_download as planet


def plot_histogram(filename, only_downloaded=False):
    with open(filename, "r") as f:
        items = json.load(f)
    name = planet.get_config_basename(filename)

    if only_downloaded:
        timestamps = [
            datetime.strptime(ts["properties"]["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ")
            for ts in items["results"]
            if planet.check_existence(ts["id"], items["config"]["download_path"])
        ]
    else:
        timestamps = [
            datetime.strptime(ts["properties"]["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ")
            for ts in items["results"]
        ]

    df = pd.DataFrame(timestamps, columns=["timestamp"])
    doy = df.groupby(df["timestamp"].dt.dayofyear)

    fig, ax = plt.subplots(figsize=(3 + len(doy) / 5, 5), tight_layout=True)
    doy.count().plot(ax=ax, kind="bar")
    ax.set_title(f"{items['config']['description']} ({len(timestamps)} images)")
    ax.set_ylabel("Number of images")
    ax.set_xlabel("Day of year")

    fig.savefig(name + "-histogram.pdf", dpi=300)

    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json [-d]")
        print("")
        print("     -d  Only plot downloaded images")
        exit(1)
   
    only_downloaded = False
    if len(sys.argv) > 2 and sys.argv[2] == "-d":
        only_downloaded = True

    plot_histogram(sys.argv[1], only_downloaded)
