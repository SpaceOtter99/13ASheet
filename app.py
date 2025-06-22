# app.py
from flask import (
    Flask, render_template, request,
    make_response, redirect, url_for, jsonify
)
import jsonpickle
from data import User, Character

def create_app():
    app = Flask(__name__)

    def load_data() -> User:
        raw = request.cookies.get('user_data')
        try:
            return jsonpickle.decode(raw) if raw else User()
        except ValueError:
            return User()

    def save_and_respond(data, response):
        response.set_cookie('user_data', jsonpickle.encode(data))
        return response

    @app.route('/', methods=['GET', 'POST'])
    def hello():
        if request.method == 'POST':
            resp = make_response(render_template('index.html'))
            resp.delete_cookie("user_data")
            return resp
        data = load_data()
        resp = make_response(render_template('index.html'))
        return save_and_respond(data, resp)

    @app.route('/sheets', methods=['GET', 'POST'])
    def sheets():
        data = load_data()
        # now a dict: name -> Character
        sheets = data.sheets

        if request.method == 'POST':
            name = request.form['name'].strip()
            if name and name not in sheets:
                sheets[name] = Character(name)
                data.sheets = sheets
            resp = make_response(redirect(url_for('sheets')))
            return save_and_respond(data, resp)

        # pass the dict itself or its values() into the template
        return render_template('sheets.html', characters=sheets)

    @app.route('/sheets/<name>')
    def sheet(name):
        data = load_data()
        character = data.sheets.get(name)
        if not character:
            return "Sheet not found", 404
        return render_template('sheet.html', data=data, character=character)

    @app.route('/sheets/<name>/data')
    def get_character_data(name):
        data = load_data()
        character = data.sheets.get(name)
        if not character:
            return jsonify({'error': 'Sheet not found'}), 404

        return jsonify({
            'stats': {
                **{
                    f"stat-{stat}": val
                    for stat, val in character.stats.items()
                },
                **{
                    f"mod-{stat}": character.modifier(stat)
                    for stat in character.stats
                }
            },
            'defences': {
                'stats': {
                    **{
                        f"stat-{d}": character.get_defence_stat(d)
                        for d in character.defences
                    },
                    **{
                        f"bonus-{d}": character.get_defence_bonus(d)
                        for d in character.defences
                    },
                    **{
                        f"final-{d}": character.get_defence(d)
                        for d in character.defences
                    }
                }
            }
        })

    @app.route('/sheets/<name>/update', methods=['POST'])
    def update_character(name):
        data = load_data()
        character = data.sheets.get(name)
        if not character:
            return jsonify({'error': 'Sheet not found'}), 404

        payload = request.get_json() or {}
        for stat, val in payload.get("stats", {}).items():
            if stat.startswith("base-"):
                key = stat.split("-", 1)[1]
                character.stats[key] = val

        for defence, val in payload.get("defences", {}).items():
            if defence.startswith("base-"):
                key = defence.split("-", 1)[1]
                character.defences[key].base = val

        data.sheets[name] = character
        resp = jsonify({'status': 'ok'})
        return save_and_respond(data, resp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
