from flask import Flask, render_template, request
from werkzeug import secure_filename
import db
import os, sys, json
import time

UPLOAD_FOLDER = "traces/"

app = Flask(__name__)
db = db.get_db()


@app.route('/')
def home():
	return render_template('index.html')


@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		files = request.files.getlist("files[]")
		print(files)
		d = {"files":[]}
		for f in files:
			filename = secure_filename(f.filename)
			# save the file
			path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			if os.path.isfile(path):
				continue

			# save file in UPLOAD_FOLDER and send mail
			f.save(path)
			process_new_logs(db, path)
			d["files"].append({"name": filename})

	return json.dumps(d)


# start the server with the 'run()' method
if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)
