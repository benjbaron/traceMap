from flask import Flask, render_template, request
from werkzeug import secure_filename
import os, sys, json
import time
import process
import db


UPLOAD_FOLDER = "traces/"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

trace_db = db.get_db()


@app.route('/')
def home():
	return map()


@app.route('/map')
def map():
	return render_template('index.html')


@app.route('/tracelist')
def trace_list():
	return render_template('tracelist.html')


@app.route('/gettraces')
def get_traces():
	return json.dumps(db.get_traces(trace_db))


@app.route('/gettraceslist')
def get_traces_list():
	return json.dumps(db.get_traces_list(trace_db))


@app.route('/deletetrace', methods = [ 'POST' ])
def delete_trace():
	if request.method == 'POST':
		trace_id = request.json['trace_id']
		user_id = request.json['user_id']
		return json.dumps(db.delete_trace(trace_db, trace_id, user_id))


@app.route('/showtrace', methods = [ 'GET', 'POST' ])
def show_trace():
	if request.method == 'GET':
		print(request.args)
		trace_id = request.args.get('trace_id')
		user_id = request.args.get('user_id')
		trace_type = request.args.get('type')
		return json.dumps(db.get_trace(trace_db, trace_id, user_id, trace_type))


@app.route('/processtrace', methods = [ 'GET', 'POST' ])
def process_trace():
	trace_id = ""
	user_id = ""
	path = ""
	process = False
	if request.method == 'POST':
		trace_id = request.json['trace_id']
		user_id = request.json['user_id']
		path = request.json['path']
		process = request.json['process']

		db.process_new_trace(trace_db, path, trace_id, user_id, process)
	
	return json.dumps({"trace_id": trace_id, "user_id": user_id})


@app.route('/upload', method = ['POST'])
def upload():
	data = request.json
	print(data)
	return json.dumps({'submitted': 'ok'})


@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
	print("upload file " + request.method)
	d = {"files":[]}
	if request.method == 'POST':
		files = request.files.getlist("files[]")
		print(files)
		for f in files:
			filename = secure_filename(f.filename)
			name, ext = os.path.splitext(filename)
			# save the file
			path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			if os.path.isfile(path):
				continue

			# save file in UPLOAD_FOLDER
			f.save(path)
			ids = process.get_user_ids(path)

			d["files"].append({"filename": filename, "ids": ids, "path": path, "name": name, "ext": ext})

	return json.dumps(d)


# start the server with the 'run()' method
if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)
