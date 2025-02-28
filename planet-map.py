#!/usr/bin/env python
# %%
import json
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from shapely.geometry.polygon import Polygon

import planet_download as planet


def plot_map(filename):
    with open(filename, "r") as f:
        items = json.load(f)
    name = planet.get_config_basename(filename)

    locations = [Polygon(ts["geometry"]["coordinates"][0]) for ts in items["results"]]

    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_extent(
        [
            items["config"]["area_lon1"] - 1,
            items["config"]["area_lon2"] + 1,
            items["config"]["area_lat1"] - 1,
            items["config"]["area_lat2"] + 1,
        ],
        crs=ccrs.PlateCarree(),
    )

    ax.add_geometries(
        locations,
        crs=ccrs.PlateCarree(),
        facecolor="None",
        edgecolor="#DD4444",
        alpha=0.8,
        rasterized=True,
    )
    ax.add_geometries(
        [Polygon(planet.get_polygon_from_config(items["config"]))],
        crs=ccrs.PlateCarree(),
        facecolor="None",
        edgecolor="#4444DD",
        alpha=0.8,
        rasterized=True,
    )

    ax.gridlines(visible=False, draw_labels=True)

    ax.add_feature(cfeature.COASTLINE)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"{items['config']['description']} ({len(locations)} images)")

    fig.savefig(name + "-map.pdf", dpi=300)

    plt.show()

    # %%


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json")
        exit(1)

    plot_map(sys.argv[1])
