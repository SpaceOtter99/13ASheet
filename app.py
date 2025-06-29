import os
import json
import copy

import uuid
from flask import (
    Flask, render_template, request,
    make_response, redirect, url_for, jsonify
)
import jsonpickle
from attrdict import AttrDict
from data import STATS, DEFENCES

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "default_sheet.json"), "r", encoding="utf-8") as f:
    DEFAULT_SHEET = json.load(f)

def create_app():
    app = Flask(__name__)
    app.jinja_env.globals.update(STATS=STATS, DEFENCES=DEFENCES)


    def load_data() -> AttrDict:
        raw = request.cookies.get('user_data')
        try:
            top = AttrDict(jsonpickle.decode(raw)) if raw else AttrDict({'sheets': {}})
        except (ValueError, TypeError):
            top = AttrDict({'sheets': {}})

        # now wrap each sheet in an AttrDict
        wrapped = {}
        for name, sheet in top.sheets.items():
            wrapped[name] = AttrDict(sheet)
        top.sheets = wrapped
        return top


    def save_and_respond(data: AttrDict, response):
        response.set_cookie('user_data', jsonpickle.encode(data))
        return response

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            resp = make_response(render_template('index.html'))
            resp.delete_cookie('user_data')
            return resp
        data = load_data()
        resp = make_response(render_template('index.html', user=data))
        return save_and_respond(data, resp)

    @app.route('/sheets', methods=['GET', 'POST'])
    def sheets():
        data = load_data()
        print(str(data))
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            id = str(uuid.uuid4())
            if id and id not in data.sheets:
                data.sheets[id] = copy.deepcopy(DEFAULT_SHEET)
                data.sheets[id].basic.name = name
            resp = make_response(redirect(url_for('sheet', id=id)))
            return save_and_respond(data, resp)
        return render_template('sheets.html', data=data.sheets)

    @app.route('/sheets/<id>', methods=['GET'])
    def sheet(id):
        data = load_data()
        if id not in data.sheets:
            return jsonify(data), 404
        character = data.sheets.get(id)
        return render_template('sheet.html', character=character)

    @app.route('/sheets/<id>/data', methods=['GET'])
    def get_character_data(id):
        data = load_data()
        character = data.sheets.get(id)
        if not character:
            return jsonify({'error': 'Sheet not found'}), 404
        return jsonify(character.to_dict())

    @app.route('/sheets/<id>/update', methods=['POST'])
    def update_character(id):
        data      = load_data()
        character = data.sheets.get(id)
        if not character:
            return jsonify({'error': 'Sheet not found'}), 404

        payload = request.get_json().get('updates', {}) or {}

        for section, entries in payload.items():
            if isinstance(entries, list):
                lst = character.setdefault(section, [])
                if not isinstance(lst, list):
                    lst = []
                    character[section] = lst

                for idx, fields in enumerate(entries):
                    if not isinstance(fields, dict):
                        continue
                    while len(lst) <= idx:
                        lst.append({})
                    for field, val in fields.items():
                        lst[idx][field] = val

            else:
                sec = character.setdefault(section, {})
                for data_key, value in entries.items():
                    parts = data_key.split('-', 1)
                    if len(parts) > 1:
                        outer, inner = parts
                        bucket = sec.setdefault(outer, {})
                        bucket[inner] = value
                    else:
                        sec[parts[0]] = value

        for section, lst in list(character.items()):
          if isinstance(lst, list):
              cleaned = []
              for entry in lst:
                  if any(str(v).replace("0","").strip() for v in entry.values()):
                      cleaned.append(entry)
              character[section] = cleaned

        data.sheets[id] = character
        resp = jsonify({'status': 'ok'})
        return save_and_respond(data, resp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)