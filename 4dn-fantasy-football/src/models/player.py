class Player:
    def __init__(self, name, team, position, projected_points):
        self.name = name
        self.team = team
        self.position = position
        self.projected_points = projected_points

    def to_dict(self):
        return {
            "name": self.name,
            "team": self.team,
            "position": self.position,
            "projected_points": self.projected_points
        }