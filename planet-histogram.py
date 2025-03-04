#!/usr/bin/env python
# %%
import json
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

import planet_download as planet

COLOR_AVAILABLE = "#aadd88"
COLOR_DOWNLOADED = "#66aa44"


def plot_histogram(filename, downloaded=False, granularity="day"):
    with open(filename, "r") as f:
        items = json.load(f)
    name = planet.get_config_basename(filename)

    timestamps_dl = [
        datetime.strptime(ts["properties"]["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ")
        for ts in items["results"]
        if planet.check_existence(ts["id"], items["config"]["download_path"])
    ]
    timestamps = [
        datetime.strptime(ts["properties"]["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ")
        for ts in items["results"]
    ]

    df = pd.DataFrame(timestamps, columns=["timestamp"])
    if granularity == "day":
        counts = df.groupby(df["timestamp"].dt.dayofyear)
    else:
        counts = df.groupby(df["timestamp"].dt.month)

    if downloaded:
        df_dl = pd.DataFrame(timestamps_dl, columns=["timestamp"])
        if granularity == "day":
            counts_dl = df_dl.groupby(df_dl["timestamp"].dt.dayofyear)
        else:
            counts_dl = df_dl.groupby(df_dl["timestamp"].dt.month)
    else:
        counts_dl = []

    fig, ax = plt.subplots(
        figsize=(3 + max(len(counts_dl), len(counts)) / 5, 5), tight_layout=True
    )
    counts.count().plot(ax=ax, kind="bar", label="available", color=COLOR_AVAILABLE)
    if downloaded:
        counts_dl.count().plot(ax=ax, kind="bar", color=COLOR_DOWNLOADED)
        ax.legend(["available", "downloaded"])
        ax.set_title(
            f"{items['config']['description']} ({len(timestamps_dl)} out of {len(timestamps)} images)"
        )
    else:
        ax.legend(["available"])
        ax.set_title(f"{items['config']['description']} ({len(timestamps)} images)")
    ax.set_ylabel("Number of images")
    ax.set_xlabel(f"By {granularity}")

    fig.savefig(name + "-histogram.pdf", dpi=300)

    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json [-d] [-m]")
        print("")
        print("     -d  Show statistics for downloaded image as well")
        print("     -m  Group by month (Default: By day of year)")
        exit(1)

    downloaded = False
    granularity = "day"
    for arg in sys.argv[2:]:
        if arg == "-d":
            downloaded = True
        if arg == "-m":
            granularity = "month"

    plot_histogram(sys.argv[1], downloaded, granularity)
