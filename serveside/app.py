import json

import sever_info
from flask import Flask, request, abort

app = Flask(__name__)


@app.route('/temperature', methods=['GET'])
def temperature():
    return sever_info.get_temperature()


@app.route('/sensors', methods=['GET'])
def sensors():
    return json.dumps(sever_info.get_sensors())


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
