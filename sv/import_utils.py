import requests
import re

def _get_get_data_from_insee_code(insee_code):
    response = requests.get(f"https://geo.api.gouv.fr/communes/{insee_code}?fields=departement")
    data = response.json()
    return {"name": data["nom"], "code": data["code"], "departement":data["departement"]["nom"]}


def _get_get_data_from_city_name(name):
    response = requests.get(f"https://geo.api.gouv.fr/communes?nom={name}&fields=departement")
    data = response.json()
    if not data:
        return None
    return {"name": data[0]["nom"], "code": data[0]["code"], "departement":data[0]["departement"]["nom"]}


def get_geo_data(data):
    try:
        insee_code = int(data)
        return _get_get_data_from_insee_code(insee_code)
    except ValueError:
        name = data
        return _get_get_data_from_city_name(name)


def get_geo_position(lat, long):
    if "X" in lat and "Y" in long:
        coord_1 = lat.replace("X", "").replace(":", "").replace(" ", "").replace("Y", "").replace(",", ".")
        coord_2 = long.replace("Y", "").replace(":", "").replace(" ", "").replace("X", "").replace(",", ".")
        try:
            if float(coord_1) > 200000 and float(coord_2)> 6000000:
                return {"lambert93_latitude": coord_2, "lambert93_longitude":coord_1}
            if float(coord_2) > 200000 and float(coord_1)> 6000000:
                return {"lambert93_latitude": coord_1, "lambert93_longitude":coord_2}
        except ValueError:
            return None
        return None
    if "°" in lat and "°" in long:
        lat = lat.replace("'' ", '"').replace("′","'").replace(" ", "").replace("″", '"')
        deg, minutes, seconds, direction = re.split('[°\'"]', lat)
        new_lat = (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)

        long = long.replace("'' ", '"').replace("′","'").replace(" ", "").replace("″", '"')
        deg, minutes, seconds, direction = re.split('[°\'"]', long)
        new_long = (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)
        return {"wgs84_longitude": new_long, "wgs84_latitude": new_lat}

    if "," in lat and "," in long:
        try:
            return {"wgs84_longitude": float(long.replace(",",".")), "wgs84_latitude": float(lat.replace(",","."))}
        except ValueError:
            return None

    if "." in lat and "." in long:
        try:
            return {"wgs84_longitude": float(long), "wgs84_latitude": float(lat)}
        except ValueError:
            return None
