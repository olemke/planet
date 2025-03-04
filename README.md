# Python scripts for downloading Planet images

Scripts have to be run from the root of the repository.

The scripts requires an API key to be stored as an environment variable called `PL_API_KEY`.

```bash
export PL_API_KEY="YOUR_API_KEY"
```

## Configuration
The scripts require a configuration file in JSON format. The configuration file should contain the following fields:

- `name`: name of the configuration
- `description`: description of the configuration, used as title in plotting scripts
- `download_path`: path to the directory where the images will be downloaded, absolute or relative to the current directory
- `area_lat1`: latitude of the top left corner of the area
- `area_lat2`: latitude of the bottom right corner of the area
- `area_lon1`: longitude of the top left corner of the area
- `area_lon2`: longitude of the bottom right corner of the area
- `starttime`: start time of the search in the format `[year, month, day]`
- `endtime`: end time of the search in the format `[year, month, day]`
- `item_type`: type of the items to search for
- `filters`: list of filters to apply to the search results (see [Planet documentation](https://developers.planet.com/docs/apis/data/searches-filtering/) for more information)

See `barbados-large-config.json` for an example configuration.

The GeometryFilter is constructed from the `area_lat1`, `area_lat2`, `area_lon1`, and `area_lon2` fields. The `area_*` fields are automatically ignored if a custom GeometryFilter is specified in the `filters` field.

## Search/selection
This script searches for Planet images and saves the results in a JSON file `NAME-results.json` in the current directory. NAME is specified in the `name` field of the configuration file.

```bash
python planet-search.py barbados-large-config.json
```

This will create a JSON file called `barbados-large-results.json` in the current directory.

## Downloading
This script downloads the images from the JSON file created by `planet-search.py`.

```bash
python planet-download.py barbados-large-results.json [-r]
```

This will download the images to the `barbados` directory as specified in `barbados-large-config.json`.

`-r` can be added as a second parameter to download images in random order.

## Additional scripts

### Number of files per day of the year

This script plots a histogram with the number of images found for each day of the year.

```bash
python plot-histogram.py barbados-large-results.json [-d]
```

`-d` as a second paramter will only respect already download images for the statistics.

### Map of the locations of the found images

This script plots the locations of the images found in the JSON file created by `planet-search.py`.

```bash
python plot-map.py barbados-large-results.json [-d]
```

`-d` as a second parameter will only plot locations for already downloaded images.

### Area of found images

This script calculates the geodesic area in km^2 of the images found in the JSON file created by `planet-search.py`.

```bash
python planet-calculate-area.py barbados-large-results.json
```