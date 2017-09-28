## traceMap

traceMap is a service that allows representing spatio-temporal traces (e.g., GPS
traces) on an interactive map. 

The service is hosted on Heroku: https://tracemap.herokuapp.com
The MongoDB is hosted on mlab: mongodb://tracemap:tracemap@ds151014.mlab.com:51014/tracemap

Here are some information related to the use of the service:
- The spatiotemporal trace data must be of format `id timestamp lon lat`
- The spatiotemporal points of the trace data must be ordered by timestamp (from oldest to newest)
- To add a new trace, go to the "Trace list" menu and upload the new trace
- The data is automatically processed by the backend server to aggregate the points that have the same coordinates _in sequence_