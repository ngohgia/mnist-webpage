import os
import numpy as np
import requests
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 3 * 1000 * 1000 # 3MB
app.add_url_rule(
    "/uploads/<name>", endpoint="display_image", build_only=True
)

# TO BE SET
app.secret_key = b'_@#52AAaw_please_change_this_to_any_random_string'
app.config["QUERY_URL"] = "google_cloud_function_http_endpoint"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(filepath):
    NEW_SIZE = (28, 28)
    MEAN = 0.1307
    STD  = 0.3081

    im = Image.open(filepath).convert('L') # load and convert to greyscale
    im = im.resize(NEW_SIZE)
    im = np.expand_dims(np.asarray(im), axis=0)

    im = ((im / np.max(im) - MEAN) / STD).tolist()
    return im

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        payload = { "features": preprocess_image(filepath) }
        try:
            r = requests.post(app.config["QUERY_URL"], json=payload).json()
            return render_template('index.html', filename=filename, pred=r["result"])
        except Exception as err:
            flash(err)
        
        return render_template('index.html', filename=filename)
    flash('Allowed image types are png, jpg, jpeg, gif')
    return redirect(request.url)

@app.route('/uploads/<filename>')
def display_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
