from __future__ import division
from math import radians, cos, sin, asin, sqrt
import sys
import datetime


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Source: https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r


def create_geojson_feature(properties, geom_type, coordinates):
    s = """
        {
            "type": "Feature",
            "properties": {"""

    count = 0
    for k, v in properties.items():
        s += """
                "{key}": {value}""".format(key=k, value=v)
        if count != len(properties)-1:
            s += ","
        count += 1
    s += """
            }}, 
            "geometry": {{
                "type": "{type}",
                "coordinates": [
                    {coordinates}
                ]
            }}
        }}""".format(type=geom_type, coordinates=", ".join(str(e) for e in coordinates))

    return s


def create_place_feature(ts_start, ts_end, pid, x, y):
        s = """
        {{
            "type": "Feature",
            "properties": {{
                "ts_start": {ts_start},
                "ts_end": {ts_end},
                "id": "{pid}",
                "dur": {dur}
            }},
            "geometry": {{
                "type": "Point",
                "coordinates": [
                    {y},
                    {x}
                ]
            }}
        }}""".format(ts_start=ts_start, ts_end=ts_end, pid=pid, dur=(ts_end-ts_start), x=x, y=y)

        return s


def create_movement_feature(ts_start, ts_end, pid, x1, y1, x2, y2):
        distance = haversine(y1,x1,y2,x2)
        duration = ts_end-ts_start
        speed = 1e10 if duration == 0 else (distance*1000)/(duration/1000)
        s = """
        {{
            "type": "Feature",
            "properties": {{
                "ts_start": {ts_start},
                "ts_end": {ts_end},
                "id": "{pid}",
                "dur": {dur},
                "distance": {dist},
                "speed": {speed}
            }},
            "geometry": {{
                "type": "LineString",
                "coordinates": [
                    [
                        {y1},
                        {x1}
                    ],
                    [
                        {y2},
                        {x2}
                    ]
                ]
            }}
        }}""".format(ts_start=ts_start, ts_end=ts_end, pid=pid, dur=duration, 
                x1=x1, y1=y1, x2=x2, y2=y2, dist=distance, speed=speed)

        return s


def write_start_geojson(file):
    file.write("""
{
    "type": "FeatureCollection",
    "features": [""")


def start_geojson():
    return """
{
    "type": "FeatureCollection",
    "features": ["""


def write_end_geojson(file):
    file.write("""
    ]
}""")


def end_geojson():
    return """
    ]
}"""


def timestamp_to_datetime(ts):
        """ 
        Return the datetime string from the timestamp "ts"
        """
        return datetime.datetime.fromtimestamp(ts/1000).strftime("%d/%m/%y %H:%M:%S")