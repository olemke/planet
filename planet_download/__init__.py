import datetime as dt
import os
from glob import glob
from time import sleep

import requests
import wget
from requests.auth import HTTPBasicAuth


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
        print(f"{id0} downloading...")

    # Returns JSON metadata for assets in this ID. Learn more: planet.com/docs/reference/data-api/items-assets/#asset
    result = requests.get(id0_url, auth=HTTPBasicAuth(api_key, ""))

    if "ortho_analytic_8b" in result.json():
        # Parse out useful links
        links = result.json()["ortho_analytic_8b"]["_links"]
        self_link = links["_self"]
        activation_link = links["activate"]

        # Request activation of the 'ortho_analytic_4b' asset:
        activate_result = requests.get(activation_link, auth=HTTPBasicAuth(api_key, ""))

        # print(activation_status_result.json()["status"])

        asset_activated = False

        starttime = dt.datetime.now()
        while not asset_activated:
            # Send a request to the item's assets url
            activation_status_result = requests.get(
                self_link, auth=HTTPBasicAuth(api_key, "")
            )

            # Assign a variable to the item's assets url response
            assets = activation_status_result.json()

            # # Assign a variable to the basic_analytic_4b asset from the response
            # visual = assets["ortho_analytic_8b"]

            asset_status = activation_status_result.json()["status"]

            # If asset is already active, we are done
            if asset_status == "active":
                asset_activated = True
                print(f"Asset {id0} is active and ready to download")
            else:
                print(f"Asset {id0} is not active yet, status: {asset_status}")
                sleep(5)

        print(f"Time taken for activation of {id0}: {dt.datetime.now() - starttime}")

        starttime = dt.datetime.now()
        # Image can be downloaded by making a GET with your Planet API key, from here:
        download_link = activation_status_result.json()["location"]

        print(f"Download of {id0} started")
        wget.download(download_link, config["download_path"], bar=None)

        # Parse out useful links
        links_metadata = result.json()["ortho_analytic_8b_xml"]["_links"]
        self_link_metadata = links_metadata["_self"]
        activation_link_metadata = links_metadata["activate"]

        # Request activation of the 'ortho_analytic_4b' asset:
        activate_result_metadata = requests.get(
            activation_link_metadata, auth=HTTPBasicAuth(api_key, "")
        )

        activation_status_result_metadata = requests.get(
            self_link_metadata, auth=HTTPBasicAuth(api_key, "")
        )
        print(activation_status_result_metadata.json()["status"])

        # Image can be downloaded by making a GET with your Planet API key, from here:
        download_link_metadata = activation_status_result_metadata.json()["location"]
        ################ ! #################
        ####### change the save path #######
        ################ ! #################
        wget.download(download_link_metadata, config["download_path"], bar=None)

        print(
            f"Finished {id0}, time taken for download: {dt.datetime.now() - starttime}"
        )
