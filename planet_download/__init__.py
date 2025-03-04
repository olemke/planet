import datetime as dt
import os
from glob import glob
from time import sleep

import requests
import wget
from requests.auth import HTTPBasicAuth


def get_config_basename(configfile):
    return (
        configfile.replace("-config", "").replace("-results", "").replace(".json", "")
    )


def calc_total_area(items):
    from pyproj import Geod
    from shapely.geometry.polygon import Polygon

    locations = [Polygon(ts["geometry"]["coordinates"][0]) for ts in items["results"]]

    geod = Geod(ellps="WGS84")
    return sum(abs(geod.geometry_area_perimeter(loc)[0]) for loc in locations)


def create_geometry_filter(lat1, lat2, lon1, lon2):
    geojson_geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [lon1, lat1],
                [lon1, lat2],
                [lon2, lat2],
                [lon2, lat1],
                [lon1, lat1],
            ]
        ],
    }
    return {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": geojson_geometry,
    }


def get_polygon_from_config(config):
    return create_geometry_filter(
        config["area_lat1"],
        config["area_lat2"],
        config["area_lon1"],
        config["area_lon2"],
    )["config"]["coordinates"][0]


def build_filelist(
    config,
    api_key=os.getenv("PL_API_KEY"),
    depth=0,
    starttime=None,
    endtime=None,
):
    if api_key is None:
        raise ValueError("API key not found")
    if starttime is None:
        starttime = dt.datetime(*config["starttime"])
    if endtime is None:
        endtime = dt.datetime(*config["endtime"])

    if (endtime - starttime).total_seconds() < 60:
        raise RuntimeError(f"Search interval got too small: {starttime, endtime}")
    depth += 1
    items = search(config, api_key, starttime, endtime)
    print(
        f"Searched period {starttime, endtime}, found {len(items)} items (depth {depth})"
    )
    sleep(0.3)

    if len(items) >= 250:
        half_step = endtime - (endtime - starttime) / 2
        first_half = build_filelist(config, api_key, depth, starttime, half_step)
        second_half = build_filelist(config, api_key, depth, half_step, endtime)
        items = first_half + second_half

    return items


def search(config, api_key=os.getenv("PL_API_KEY"), starttime=None, endtime=None):
    if api_key is None:
        raise ValueError("API key not found")
    if starttime is None:
        starttime = dt.datetime(*config["starttime"])
    if endtime is None:
        endtime = dt.datetime(*config["endtime"])
    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": starttime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lte": endtime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }

    geometry_filter = create_geometry_filter(
        config["area_lat1"],
        config["area_lat2"],
        config["area_lon1"],
        config["area_lon2"],
    )

    combined_filter = {
        "type": "AndFilter",
        "config": [
            date_range_filter,
        ]
        + config["filters"],
    }

    custom_geometry = False
    for f in config["filters"]:
        if f["type"] == "GeometryFilter":
            custom_geometry = True
            break

    if not custom_geometry:
        combined_filter["config"].append(geometry_filter)

    if api_key is None:
        raise ValueError("API key not found")

    # API request object
    search_request = {"item_types": [config["item_type"]], "filter": combined_filter}

    # fire off the POST request
    delay = 1
    success = False
    while not success:
        try:
            search_result = requests.post(
                "https://api.planet.com/data/v1/quick-search",
                auth=HTTPBasicAuth(api_key, ""),
                json=search_request,
            )
            success = True
        except requests.exceptions.ConnectionError:
            print(f"Connection error, retrying in {delay} seconds")
            sleep(delay)
            delay *= 2
            continue

    # print(search_result.json())
    return search_result.json()["features"]


def check_existence(id0, download_path):
    return len(glob(os.path.join(download_path, id0) + "*.[xt][mi][lf]")) == 2


def download_image(id0, config, api_key=os.getenv("PL_API_KEY")):
    if api_key is None:
        raise ValueError("API key not found")

    os.makedirs(config["download_path"], exist_ok=True)

    id0_url = "https://api.planet.com/data/v1/item-types/{}/items/{}/assets".format(
        config["item_type"], id0
    )
    if check_existence(id0, config["download_path"]):
        print(f"{id0} already downloaded")
        return
    else:
        print(f"{id0} queued for download")

    # Returns JSON metadata for assets in this ID. Learn more: planet.com/docs/reference/data-api/items-assets/#asset
    result = requests.get(id0_url, auth=HTTPBasicAuth(api_key, ""))

    if "ortho_analytic_8b" in result.json():
        image_type = "ortho_analytic_8b"
    elif "ortho_analytic_4b" in result.json():
        image_type = "ortho_analytic_4b"
    else:
        print(f"{id0} has no usable asset")
        return

    # Parse out useful links
    links = result.json()[image_type]["_links"]
    self_link = links["_self"]
    activation_link = links["activate"]

    # Request activation of the asset:
    requests.get(activation_link, auth=HTTPBasicAuth(api_key, ""))

    # print(activation_status_result.json()["status"])

    asset_activated = False

    starttime = dt.datetime.now()
    waitcycles = 0
    waittime = 10
    maxcycles = 900 // waittime  # Maximum time to wait for activation
    retry_failed_activation = True
    while not asset_activated:
        # Send a request to the item's assets url
        activation_status_result = requests.get(
            self_link, auth=HTTPBasicAuth(api_key, "")
        )

        asset_status = activation_status_result.json()["status"]

        # If asset is already active, we are done
        if asset_status == "active":
            asset_activated = True
            print(
                f"{id0} is active and ready to download, took {dt.datetime.now() - starttime}"
            )
        # if the asset is inactive, try activation once again
        elif asset_status == "inactive" and retry_failed_activation:
            print(f"{id0} status is inactive, retrying activation")
            requests.get(activation_link, auth=HTTPBasicAuth(api_key, ""))
            retry_failed_activation = False
            sleep(waittime)
        # give up if asset is still inactive after second activation attempt
        elif asset_status == "inactive" and not retry_failed_activation:
            print(f"{id0} status is inactive, skipping, rerun script to try again")
            return
        # if asset has not activated after maximum waittime, give up
        elif waitcycles >= maxcycles:
            print(
                f"{id0} activation took too long, skipping, rerun script to try again"
            )
            return
        # output status every minute while waiting for activation
        else:
            if waitcycles % (60 // waittime) == 0:
                print(f"{id0} is not active yet, status: {asset_status}")
            waitcycles += 1
            sleep(waittime)

    starttime = dt.datetime.now()
    # Image can be downloaded by making a GET with your Planet API key, from here:
    download_link = activation_status_result.json()["location"]

    print(f"{id0} download started")
    wget.download(download_link, config["download_path"], bar=None)

    # Parse out useful links
    links_metadata = result.json()[image_type + "_xml"]["_links"]
    self_link_metadata = links_metadata["_self"]
    activation_link_metadata = links_metadata["activate"]

    # Request activation of the 'ortho_analytic_4b' asset:
    requests.get(activation_link_metadata, auth=HTTPBasicAuth(api_key, ""))

    activation_status_result_metadata = requests.get(
        self_link_metadata, auth=HTTPBasicAuth(api_key, "")
    )
    print(
        f"{id0} metadata activation status: {activation_status_result_metadata.json()['status']}"
    )

    # Image can be downloaded by making a GET with your Planet API key, from here:
    download_link_metadata = activation_status_result_metadata.json()["location"]
    wget.download(download_link_metadata, config["download_path"], bar=None)

    print(f"{id0} finished, time taken for download: {dt.datetime.now() - starttime}")
