from flask import Blueprint, jsonify

projections_bp = Blueprint('projections', __name__)

@projections_bp.route('/api/projections', methods=['GET'])
def get_projections():
    sample_players = [
        {"name": "Player One", "team": "Team A", "position": "QB", "projected_points": 25},
        {"name": "Player Two", "team": "Team B", "position": "RB", "projected_points": 20},
        {"name": "Player Three", "team": "Team C", "position": "WR", "projected_points": 18},
        {"name": "Player Four", "team": "Team D", "position": "TE", "projected_points": 15},
        {"name": "Player Five", "team": "Team E", "position": "DEF", "projected_points": 10}
    ]
    return jsonify(sample_players)