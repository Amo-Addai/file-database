from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import json

from server import Server

ALLOWED_EXTENSIONS = set(['xls', 'xlsx', 'csv', 'json', 'xml', 'txt', 'pdf'])
CATEGORIES = set(['All'])

app = Flask(__name__)
server = Server()
app = server.setup_db_and_file_system(app)
print("Server, Database, and File System have all been set up successfully!!")
print()
default_filter, default_category, default_collection, default_filename, default_file_type = None, "All", "Examination", "", ""
request_data, response_message, response_data = {}, "Sorry, some error occurred.", {}


def get_request_data():
    global request_data
    data = request_data
    request_data = {}
    return data


def get_response_message():
    global response_message
    msg = response_message
    response_message = "Sorry, some error occurred."
    return msg


def get_response_data():
    global response_data
    data = response_data
    response_data = {}
    return data


def allowed_files(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and ext in ALLOWED_EXTENSIONS, ext


def return_response(success):
    global response_message, response_data
    final_data = {'success': success, 'message': get_response_message(), 'data': get_response_data()}
    print()
    print("NOW, RETURN RESPONSE -> {}".format(final_data))
    response = app.response_class(
        response=json.dumps(final_data),
        status=200 if success else 400,
        mimetype='application/json'
    )
    return response


def render_home():
    return render_template('home.html', ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS, CATEGORIES=CATEGORIES)


@app.route('/')
def home():
    return render_home()


@app.route('/api/collections', methods=['GET'])
def get_collections_data():
    global request_data, response_message, response_data
    query = request.args if (request.args is not None) else {"category": "All"}
    if ("category" not in query) or (len(query["category"]) <= 0):
        query["category"] = "All"
    print("QUERY -> {}".format(query))
    response_data = server.get_collections(query)
    if response_data is not None:
        response_message = "Collections Available" if (len(response_data) > 0) else "No Collections Available"
    return return_response(True)


@app.route('/api/collections', methods=['DELETE'])
def delete_collection_data():
    global request_data, response_message, response_data
    if request.method == 'DELETE':
        request_data, extra = request.args, {}
        print("REQUEST -> {}".format(request_data))
        extra["category"] = default_category if (
            ("category" not in request_data) or (len(request_data["category"]) <= 0)) else request_data[
            "category"]
        if "_id" in request_data:
            extra["_id"] = request_data["_id"]
            if server.delete_collection(extra):
                response_message = "Collection deleted successfully"
                return return_response(True)
            response_message = "Collection could not be deleted successfully"
        response_message = "Collection not selected correctly"
    return return_response(False)


@app.route('/api/collections/upload', methods=['POST'])
def upload_file():  # FIND THE RIGHT WAY TO RETRIEVE request.body
    global request_data, response_message, response_data
    if request.method == 'POST':
        request_data, extra = request.form, {}
        print("REQUEST -> {}".format(request_data))
        extra["category"] = default_category if (
            ("category" not in request_data) or (len(request_data["category"]) <= 0)) else request_data[
            "category"]
        extra["collection"] = default_collection if (
            ("collection" not in request_data) or (len(request_data["collection"]) <= 0)) else request_data[
            "collection"]
        extra["filename"] = default_filename if (
            ("filename" not in request_data) or (len(request_data["filename"]) <= 0)) else request_data["filename"]
        #
        if 'file' not in request.files:
            response_message = "No file within data"
            return return_response(False)
        file = request.files['file']
        if file.filename == '':
            response_message = "No selected file"
            return return_response(False)
        file_is_allowed, extra["file_type"] = allowed_files(extra["filename"])
        #
        if file and file_is_allowed:
            filename = extra["filename"] = secure_filename(extra["filename"])
            print("Now handling file '{}' -> {}".format(filename, file))
            print("With params -> {}".format(extra))
            if server.handle_file(file, extra):
                response_message, response_data = "Server handled file '{}' successfully.".format(filename), {
                    # FIGURE OUT WHAT RESPONSE DATA TO PUT IN HERE :)
                }
                return return_response(True)
            else:
                response_message = "Server could not handle file '{}' successfully.".format(filename)
        return return_response(False)
    return return_response(False)


@app.route('/api/collections/download', methods=['PUT'])
def request_file():  # FIND THE RIGHT WAY TO RETRIEVE request.body
    global request_data, response_message, response_data
    if request.method == 'PUT':
        request_data, extra = request.json, {}
        print("REQUEST -> {}".format(request_data))
        extra["category"] = default_category if (
            ("category" not in request_data) or (len(request_data["category"]) <= 0)) else request_data[
            "category"]
        extra["collection"] = default_collection if (
            ("collection" not in request_data) or (len(request_data["collection"]) <= 0)) else request_data[
            "collection"]
        extra["filename"] = default_filename if (
            ("filename" not in request_data) or (len(request_data["filename"]) <= 0)) else request_data["filename"]
        extra["file_type"] = default_file_type if (
            ("file_type" not in request_data) or (len(request_data["file_type"]) <= 0)) else request_data[
            "file_type"]
        extra["filter"] = default_filter if (
            ("filter" not in request_data) or (len(request_data["filter"]) <= 0)) else request_data["filter"]
        #
        filename, filter = extra["filename"], extra["filter"]
        print("Now requesting file '{}'".format(filename))
        print("With parameters -> {}".format(extra))
        filepath = server.request_file(filter, extra)
        if filepath is not None:
            # uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
            # return send_from_directory(directory=uploads, filename=filename)
            response_message, response_data = "Server handled file-download request '{}' successfully".format(
                filename), {

                                              }
            return return_response(True)
        else:
            response_message = "Server could not handle file-download request '{}' successfully".format(filename)
        return return_response(False)
    return return_response(False)


if __name__ == '__main__':
    app.run()
