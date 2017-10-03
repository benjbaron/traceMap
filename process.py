import os
import sys
import datetime
import utils


class TraceStats:
    def __init__(self, starttime, endtime, nb_places, nb_movements):
        self.starttime = starttime
        self.endtime = endtime
        self.nb_places = nb_places
        self.nb_movements = nb_movements

    def __init__(self, starttime):
        self.starttime = starttime
        self.endtime = starttime
        self.nb_places = 0
        self.nb_movements = 0

    def __str__(self):
        return str(self.starttime) + " -- " + str(self.endtime) + \
            " number of places: " + str(self.nb_places) + " number of movements: " + str(self.nb_movements)


def read_file_line(line):
    fields = line.strip().split(" ")
    uid = str(fields[0])
    ts = int(fields[1])
    lon = float(fields[2])
    lat = float(fields[3])

    return uid, ts, lon, lat


def read_file_line_aggregate(line):
    fields = line.strip().split(" ")
    uid = str(fields[0])
    start_ts = int(fields[1])
    end_ts = int(fields[2])
    lon = float(fields[3])
    lat = float(fields[4])

    return uid, start_ts, end_ts, lon, lat


def get_user_ids(path):
    ids = set()
    with open(path, 'r') as f:
        for line in f:
            uid, ts, lon, lat = read_file_line(line)
            ids.add(uid)

    return list(ids)


def aggregate_trace(path, user_id):
    f_name, f_ext = os.path.splitext(path)

    geojson_pl = utils.start_geojson()
    geojson_mov = utils.start_geojson()

    with open(path, 'r') as f:
        uid, ts, lon, lat = read_file_line(f.readline())
        while uid != user_id:
            uid, ts, lon, lat = read_file_line(f.readline())
        
        starttime = ts
        endtime = ts
        pl_lon = lon
        pl_lat = lat

        stats = TraceStats(starttime)
        last = True
        for line in f:
            uid, ts, lon, lat = read_file_line(line)
            if uid != user_id:
                continue
            
            if pl_lon == lon and pl_lat == lat:
                # same point
                endtime = ts
                last = False
            else:
                if geojson_pl[-1] == "}":
                    geojson_pl += ","
                geojson_pl += utils.create_place_feature(starttime, endtime, user_id, pl_lat, pl_lon)
                if geojson_mov[-1] == "}":
                    geojson_mov += ","
                geojson_mov += utils.create_movement_feature(endtime, ts, user_id, pl_lat, pl_lon, lat, lon)
                
                last = True
                starttime = ts
                endtime = ts
                pl_lon = lon
                pl_lat = lat

                stats.nb_places += 1
                stats.nb_movements += 1

        if geojson_pl[-1] == "}":
            geojson_pl += ","
        geojson_pl += utils.create_place_feature(starttime, endtime, user_id, pl_lat, pl_lon)
        stats.nb_places += 1

        if not last:
            if geojson_mov[-1] == "}":
                geojson_mov += ","
            geojson_mov += utils.create_movement_feature(endtime, ts, user_id, pl_lat, pl_lon, lat, lon)

        stats.endtime = ts
        geojson_pl += utils.end_geojson()
        geojson_mov += utils.end_geojson()

    return geojson_pl, geojson_mov, stats


def process_trace(path, user_id):
    f_name, f_ext = os.path.splitext(path)

    geojson_pl = utils.start_geojson()
    geojson_mov = utils.start_geojson()

    with open(path, 'r') as f:
        uid, prev_start_ts, prev_end_ts, prev_lon, prev_lat = read_file_line_aggregate(f.readline())
        stats = TraceStats(prev_start_ts)
        
        for line in f:
            uid, start_ts, end_ts, lon, lat = read_file_line_aggregate(line)
            if uid != user_id:
                continue
            
            if geojson_pl[-1] == "}":
                geojson_pl += ","
            geojson_pl += utils.create_place_feature(prev_start_ts, prev_end_ts, user_id, prev_lat, prev_lon)
            if geojson_mov[-1] == "}":
                geojson_mov += ","
            geojson_mov += utils.create_movement_feature(prev_end_ts, start_ts, user_id, prev_lat, prev_lon, lat, lon)
                
            stats.nb_places += 1
            stats.nb_movements += 1
            prev_start_ts = start_ts
            prev_end_ts = end_ts
            prev_lon = lon
            prev_lat = lat

        if geojson_pl[-1] == "}":
            geojson_pl += ","
        geojson_pl += utils.create_place_feature(start_ts, end_ts, user_id, lat, lon)
        stats.nb_places += 1

        stats.endtime = end_ts
        geojson_pl += utils.end_geojson()
        geojson_mov += utils.end_geojson()

    return geojson_pl, geojson_mov, stats


if __name__ == '__main__':
    path = "traj_filtered_208150102917738_.csv"
    pl, mov, stats = process_trace(path, "208150102917738")
    print(pl)
