import sys
import json

filename = sys.argv[1]
with open(filename, 'r') as f:
	data = json.load(f)
	min_ts = 1e20
	max_ts = 0
	for feature in data['features']:
		start_ts = feature['properties']['ts_start']
		end_ts   = feature['properties']['ts_end']
		if start_ts < min_ts:
			min_ts = start_ts
		if end_ts > max_ts:
			max_ts = end_ts

print "min:", min_ts,"\nmax:", max_ts