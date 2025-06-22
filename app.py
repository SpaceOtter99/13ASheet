from flask import Flask, render_template, request, make_response, redirect, url_for, jsonify
import jsonpickle
from data import User, Character

def create_app():
    app = Flask(__name__)

    def load_data():
        raw = request.cookies.get('user_data')
        try:
            blob:User = jsonpickle.decode(raw) if raw else User()
        except ValueError:
            blob = User()
        print(blob)
        return blob

    def save_and_respond(data, response):
        response.set_cookie('user_data', jsonpickle.encode(data))
        return response

    @app.route('/', methods=['GET', 'POST'])
    def hello():
        if request.method == 'POST':
            save_and_respond({}, make_response(render_template('index.html')))
        data = load_data()
        resp = make_response(render_template('index.html'))
        return save_and_respond(data, resp)

    @app.route('/sheets', methods=['GET', 'POST'])
    def sheets():
        data = load_data()
        chars = data.sheets

        if request.method == 'POST':
            name = request.form['name'].strip()
            if name and all(c.name != name for c in chars):
                chars.append(Character(name))
                data.sheets = [c.to_dict() for c in chars]
            resp = make_response(redirect(url_for('sheets')))
            return save_and_respond(data, resp)

        return render_template('sheets.html', characters=chars)

    @app.route('/sheets/<name>')
    def sheet(name):
        data = load_data()
        chars = [Character.from_dict(d) for d in data.sheets]
        character = next((c for c in chars if c.name == name), None)
        if not character:
            return "Sheet not found", 404

        return render_template('sheet.html', data=data, character=character)

    @app.route('/sheets/<name>/update', methods=['POST'])
    def update_character(name):
        data = load_data()
        chars = [Character.from_dict(d) for d in data.sheets]
        character = next((c for c in chars if c.name == name), None)
        if not character:
            return jsonify({'error': 'Sheet not found'}), 404

        payload = request.get_json() or {}
        stats = payload.get('stats', {})
        # validate & apply
        for stat, val in stats.items():
            if stat in data.stats:
                try:
                    character.stats[stat] = int(val)
                except (TypeError, ValueError):
                    pass

        data.sheets = [c.to_dict() for c in chars]
        resp = jsonify({'status': 'ok'})
        return save_and_respond(data, resp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
