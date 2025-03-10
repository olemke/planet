#!/usr/bin/env python
# %%
import json
import sys
from datetime import datetime

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.animation as anim
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry.polygon import Polygon

import planet_download as planet


def plot_footprints(config, new_locations, locations, ax):
    ax.set_extent(
        [
            config["area_lon1"] - 1,
            config["area_lon2"] + 1,
            config["area_lat1"] - 1,
            config["area_lat2"] + 1,
        ],
        crs=ccrs.PlateCarree(),
    )

    if not locations.empty:
        ax.add_geometries(
            locations["location"],
            crs=ccrs.PlateCarree(),
            facecolor="None",
            edgecolor="#DD4444",
            alpha=0.8,
            rasterized=True,
        )

    if not new_locations.empty:
        ax.add_geometries(
            new_locations["location"],
            crs=ccrs.PlateCarree(),
            facecolor="None",
            edgecolor="#4444DD",
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
    ax.set_title(f"{config['description']}")


def animate_map(filename, id=0, downloaded=False):
    with open(filename, "r") as f:
        items = json.load(f)
    name = planet.get_config_basename(filename)

    config = items["config"]
    locations = [
        Polygon(ts["geometry"]["coordinates"][0])
        for ts in items["results"]
        if not downloaded
        or planet.check_existence(ts["id"], items["config"]["download_path"])
    ]
    timestamps = [
        datetime.strptime(ts["properties"]["acquired"], "%Y-%m-%dT%H:%M:%S.%fZ")
        for ts in items["results"]
        if not downloaded
        or planet.check_existence(ts["id"], items["config"]["download_path"])
    ]
    df = pd.DataFrame(
        {"timestamp": timestamps, "location": locations},
        columns=["timestamp", "location"],
    )

    writer = anim.writers["ffmpeg"](
        fps=15, codec="hevc", extra_args=["-tag:v", "hvc1", "-pix_fmt", "yuv420p"]
    )
    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
    with writer.saving(fig, f"{name}.mp4", 300):
        acc = pd.DataFrame()
        for g in df.groupby(df["timestamp"].dt.dayofyear):
            ax.clear()
            print(g[0])
            plot_footprints(config, g[1], acc, ax)
            ax.set_title(
                f"{config['description']} • {g[1]['timestamp'].iloc[0].strftime('%Y-%m-%d')} • {len(acc) + len(g[1])} images"
            )

            acc = pd.concat([acc, g[1]], axis=0)
            writer.grab_frame()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} SEARCH_RESULTS_FILE.json [-d]")
        print("")
        print("     -d  Plot both downloaded and available images")
        exit(1)

    downloaded = False
    if len(sys.argv) > 2 and sys.argv[2] == "-d":
        downloaded = True
    animate_map(sys.argv[1], downloaded)
