import json

import sever_info
import vpn
import qrcode
from flask import Flask, request, abort, render_template, send_file

app = Flask(__name__)


@app.route('/sensors', methods=['GET'])
def sensors():
    return json.dumps(sever_info.get_sensors())


@app.route('/add_client', methods=['GET'])
def add_client():
    res = vpn.create_client(request.args.get("name"))
    if not res:
        abort(400)
    else:
        filename = f"../wg0-client-{request.args.get('name')}"
        if request.args.get("format") == "qr":
            with open(f"{filename}.conf") as f:
                qrcode.make("\n".join(f.readlines())).save(f"{filename}.png")
                return send_file(f"{filename}.conf")
        else:
            return send_file(f"{filename}.conf")


@app.route('/get_file', methods=['GET'])
def get_file():
    filename = f"../wg0-client-{request.args.get('name')}"

    if request.args.get("format") == "qr":
        try:
            return send_file(f"{filename}.png")
        except FileNotFoundError:
            with open(f"{filename}.conf") as f:
                qrcode.make("\n".join(f.readlines())).save(f"{filename}.png")
            return send_file(f"{filename}.png")
    else:
        try:
            return send_file(f"{filename}.conf")
        except FileNotFoundError:
            abort(400)


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
