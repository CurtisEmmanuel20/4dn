from flask import Flask, jsonify
from src.api.projections import get_player_projections

app = Flask(__name__)

@app.route('/api/projections', methods=['GET'])
def projections():
    return jsonify(get_player_projections())

if __name__ == '__main__':
    app.run(debug=True)