import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    lat1, lon1, lat2, lon2 = map(math.radians, [
        float(lat1), float(lon1),
        float(lat2), float(lon2)
    ])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return round(R * c, 2)
