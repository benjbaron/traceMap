import os
from urllib.parse import urlsplit
from pymongo import MongoClient
from multiprocessing import Process
import process
import json
import time


def get_db():
    url = os.getenv('MONGO_URI', 'mongodb://localhost:27017/tracemap')
    parsed = urlsplit(url)
    db_name = parsed.path[1:]

    # Get your DB
    db = MongoClient(url)[db_name]

    # Authenticate
    if '@' in url:
        user, password = parsed.netloc.split('@')[0].split(':')
        db.authenticate(user, password)

    return db


def get_traces(db):
    l = []
    cur = db.traces.find({}, {"nb_places":1, "nb_movements":1,
        "starttime":1,"endtime":1,"trace_id":1,"user_id":1, "uptime":1})

    for doc in cur:
        l.append({
            "trace_id": doc['trace_id'],
            "user_id": doc['user_id'],
            "uptime": doc['uptime'],
            "nb_movements": doc['nb_movements'],
            "nb_places": doc['nb_places'],
            "starttime": doc['starttime'],
            "endtime": doc['endtime']
        })
    
    return l


def get_traces_list(db):
    l = {}
    cur = db.traces.find({}, {"nb_places":1, "nb_movements":1,
        "starttime":1,"endtime":1,"trace_id":1,"user_id":1, "uptime":1})
    
    for doc in cur:
        tid = doc['trace_id'] + "_" + doc['user_id']
        tid_pl = tid + "_places"
        tid_mov = tid + "_movements"
        l[tid_pl] = {
            "trace_id": doc['trace_id'],
            "user_id": doc['user_id'],
            "uptime": doc['uptime'],
            "source-id": tid_pl,
            "data-type": "geojson",
            "type": "circle",
            "nb": doc['nb_places'],
            "starttime": doc['starttime'],
            "endtime": doc['endtime'],
            "legend": {
                "key-1": {
                    "key-property": "circle-color",
                    "key-title": "Time spent at locations (seconds)"
                }
            },
            "popup": {
                "attributes": {
                    "ts_start": "dateMS",
                    "ts_end": "dateMS",
                    "dur": "timeMS"
                },
                "lnglat": True
            },
            "timeline": {
                "start": int(doc['starttime']),
                "end": int(doc['endtime']),
                "dataType": "dateMS"
            },
            "paint": {
                "circle-color": {
                    "property": "dur",
                    "stops": [
                        [0, "#FCA107"],
                        [100000, "#7F3121"]
                    ]
                },
                "circle-radius": 5
            },
            "layout": {}
        }

        l[tid_mov] = {
            "trace_id": doc['trace_id'],
            "user_id": doc['user_id'],
            "uptime": doc['uptime'],
            "source-id": tid_mov,
            "data-type": "geojson",
            "type": "line",
            "nb": doc['nb_movements'],
            "starttime": doc['starttime'],
            "endtime": doc['endtime'],
            "legend": {
                "key-1": {
                    "key-property": "line-color",
                    "key-title": "Speed between places (m/s)"
                }
            },
            "popup": {
                "attributes": {
                    "ts_start": "dateMS",
                    "ts_end": "dateMS",
                    "dur": "timeMS",
                    "speed": None
                },
                "lnglat": False
            },
            "timeline": {
                "start": int(doc['starttime']),
                "end": int(doc['endtime']),
                "dataType": "dateMS"
            },
            "paint": {
                "line-color": {
                    "property": "speed",
                    "stops": [
                        [0, "#FCA107"],
                        [100, "#7F3121"]
                    ]
                },
                "line-width": 2
            },
            "layout": {
                "line-join": "round",
                "line-cap": "round"
            }
        }

    return l


def get_trace(db, trace_id, user_id, trace_type):
    trace_filter = {"trace_id": trace_id, "user_id": user_id}
    trace_projection = {}
    trace_type_name = ""
    if trace_type == "circle":
        trace_projection["places"] = 1
        trace_type_name = "places"
    elif trace_type == "line":
        trace_projection["movements"] = 1
        trace_type_name = "movements"

    res = db.traces.find_one(trace_filter, trace_projection)
    return res[trace_type_name]



def add_trace_db(db, geojson_pl, geojson_mov, stats, trace_id, user_id):
    print("add trace to db")
    d = db.traces.find_one({'trace_id': trace_id})
    if d and d['nb_places'] > 0:
        print(trace_id + ' already in database')
        return

    d = {
        "trace_id": trace_id, 
        "user_id": user_id,
        "starttime": stats.starttime,
        "endtime": stats.endtime,
        "uptime": time.time(),
        "nb_places": stats.nb_places,
        "nb_movements": stats.nb_movements,
        "places": json.loads(geojson_pl),
        "movements": json.loads(geojson_mov)
    }

    db.traces.insert_one(d)


def process_new_trace(db, path, trace_id, user_id, proc):
    print("process trace " + path)
    if proc:
        pl, mov, stats = process.aggregate_trace(path, user_id)
    else:
        pl, mov, stats = process.process_trace(path, user_id)

    # Remove the trace after having processed it
    os.remove(path)

    # put the txt in the mongoDB database
    add_trace_db(db, pl, mov, stats, trace_id, user_id)


if __name__ == '__main__':
    db = get_db()
    trace_filter = {"trace_id": "sample_trace_5.csv", "user_id": "abdcd2"}
    trace_projection = {"places": 1}
    print(db.traces.find_one(trace_filter, trace_projection)['places'])
