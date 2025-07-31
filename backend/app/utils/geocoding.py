import requests


def get_lat_long_osm(country, city, address):
    """
    Get the latitude and longitude for a given country, city, and address using OpenStreetMap's Nominatim API.

    Args:
        country (str): The country name.
        city (str): The city name.
        address (str): The street address.

    Returns:
        tuple: A tuple containing the latitude and longitude as floats.

    Raises:
        ValueError: If any of the input parameters are empty.
        ValueError: If the geocoding request fails or returns no results.
    """
    # Validate input parameters
    if not country or not city or not address:
        raise ValueError("Country, city, and address must be provided")

    # Construct the full address
    full_address = f"{address.strip()}, {city.strip()}, {country.strip()}"

    # Construct the API URL for Nominatim
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={full_address}"

    try:
        # Make the request to the Nominatim API
        response = requests.get(url, headers={"User-Agent": "Parascope/1.0"})
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        data = response.json()

        # Check if any results were returned
        if data:
            latitude = float(data[0]["lat"])
            longitude = float(data[0]["lon"])
            #            logging.info(f"Successfully geocoded address: {full_address}")
            return latitude, longitude
        else:
            #            logging.error(f"No results found for address: {full_address}")
            raise ValueError("No results found for the provided address")

    except requests.exceptions.RequestException as e:
        #        logging.error(
        #            f"Error making request to Nominatim API for address: {full_address}, {e}"
        #        )
        raise ValueError(f"Error making request to Nominatim API: {e}")
