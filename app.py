from flask import Flask, redirect, url_for, request, render_template, session
import requests, os, uuid, json, io, time
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from PIL import Image, ImageFont, ImageDraw
from werkzeug.utils import secure_filename

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "static/img"
app.config["UPLOAD_EXTENSIONS"] = [".JPEG", ".JPG", ".PNG", ".GIF"]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')
    
@app.route('/', methods=['POST'])
def index_post():
    # Read the values from the form
    original_text = request.form['text']
    target_language = request.form['language']

    # Load the values from .env
    key = os.environ['KEY']
    endpoint = os.environ['ENDPOINT']
    location = os.environ['LOCATION']

    # Indicate that we want to translate and the API version (3.0) and the target language
    path = '/translate?api-version=3.0'
    target_language_parameter = '&to=' + target_language
    constructed_url = endpoint + path + target_language_parameter

    # Set up the header information, which includes our subscription key
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Create the body of the request with the text to be translated
    body = [{ 'text': original_text }]
    translator_request = requests.post(constructed_url, headers=headers, json=body)
    translator_response = translator_request.json()
    translated_text = translator_response[0]['translations'][0]['text']

    #Passing the translated text,original text, and target language to the template
    return render_template('translated.html',translated_text=translated_text,)

# text from image extractor
@app.route('/index2', methods=['GET'])
def index2():
    return render_template('index2.html')

def textfromimage(filename):
    # Load the values from .env
    cv_key = os.getenv('CV_KEY')
    cv_endpoint = os.getenv('CV_ENDPOINT')

    cv_client = ComputerVisionClient(cv_endpoint, CognitiveServicesCredentials(cv_key))
    local_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text_extracted =''

    response = cv_client.read_in_stream(open(local_file, 'rb'), language = 'en', raw=True)
    operationLocation = response.headers['Operation-Location']
    operation_id= operationLocation.split('/')[-1]
    time.sleep(10)
    result = cv_client.get_read_result(operation_id)

    if result.status == OperationStatusCodes.succeeded:
        read_results = result.analyze_result.read_results
        for analyzed_result in read_results:
            for line in analyzed_result.lines:
                text_extracted = text_extracted + " " + line.text

    return text_extracted

@app.route("/image", methods=['GET', 'POST'])
def main():
	return render_template("index2.html")


@app.route("/submit", methods=["GET", "POST"])
def upload_image():
    if request.method == 'POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        # if no file is uploaded
        if filename =='':
            return render_template("extracted.html", prediction = "File not selected!!")
        # checking if the file type is supported
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            print("files extension: ", file_ext)
            if file_ext.upper() not in app.config['UPLOAD_EXTENSIONS']:
                return render_template("extracted.html", prediction = "File extension not supported!!")

        # saving file to local folder
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        result = textfromimage(filename)
        return render_template("extracted.html", prediction = result)


