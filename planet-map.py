#!/usr/bin/env python
# %%
import json
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from shapely.geometry.polygon import Polygon

import planet_download as planet


def plot_footprints(config, locations, ax):
    ax.set_extent(
        [
            config["area_lon1"] - 1,
            config["area_lon2"] + 1,
            config["area_lat1"] - 1,
            config["area_lat2"] + 1,
        ],
        crs=ccrs.PlateCarree(),
    )

    if locations:
        ax.add_geometries(
            locations,
            crs=ccrs.PlateCarree(),
            facecolor="None",
            edgecolor="#DD4444",
            alpha=0.8,
            rasterized=True,
        )

    ax.add_geometries(
        [Polygon(planet.get_polygon_from_config(config))],
        crs=ccrs.PlateCarree(),
        facecolor="None",
        edgecolor="#66AA44",
        alpha=0.8,
        lw=2,
        rasterized=True,
    )

    ax.mygridliner = ax.gridlines(visible=False, draw_labels=True)

    ax.add_feature(cfeature.COASTLINE)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        f"{config['description']}" + (f"({len(locations)} images)" if locations else "")
    )


def plot_map(filename, downloaded=False):
    with open(filename, "r") as f:
        items = json.load(f)
    name = planet.get_config_basename(filename)

    if downloaded and "results" in items:
        config = items["config"]
        locations_dl = [
            Polygon(ts["geometry"]["coordinates"][0])
            for ts in items["results"]
            if planet.check_existence(ts["id"], items["config"]["download_path"])
        ]
    else:
        downloaded = False

    if "results" in items:
        config = items["config"]
        locations = [
            Polygon(ts["geometry"]["coordinates"][0]) for ts in items["results"]
        ]
    else:
        config = items
        locations = []

    if downloaded:
        fig, (ax1, ax2) = plt.subplots(
            1,
            2,
            subplot_kw={"projection": ccrs.PlateCarree()},
            layout="constrained",
            figsize=(10, 5),
            sharey=True,
        )
        plot_footprints(config, locations_dl, ax1)
        ax1.mygridliner.right_labels = False
        plot_footprints(config, locations, ax2)
        ax2.mygridliner.left_labels = False
        fig.suptitle(
            f"{config['description']} ({len(locations_dl)} out of {len(locations)} images downloaded)"
        )
        ax1.set_title("Downloaded")
        ax2.set_title("Available")
    else:
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        plot_footprints(config, locations, ax)

    fig.savefig(name + "-map.pdf", dpi=300)

    plt.show()

    # %%


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json [-d]")
        print("")
        print("     -d  Plot both downloaded and available images")
        exit(1)

    downloaded = False
    if len(sys.argv) > 2 and sys.argv[2] == "-d":
        downloaded = True
    plot_map(sys.argv[1], downloaded)
