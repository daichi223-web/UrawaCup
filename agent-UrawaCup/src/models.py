from datetime import datetime
from database import db

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_local = db.Column(db.Boolean, default=False)  # True for original 9 teams
    group = db.Column(db.String(1))  # A, B, C, D
    
    # Relationships
    standings = db.relationship('Standing', backref='team', uselist=False)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False) # 1, 2, or 3
    group = db.Column(db.String(1)) # A, B, C, D or None (for finals)
    
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    home_score = db.Column(db.Integer, default=None, nullable=True)
    away_score = db.Column(db.Integer, default=None, nullable=True)
    is_finished = db.Column(db.Boolean, default=False)

    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])

class Standing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    played = db.Column(db.Integer, default=0)
    won = db.Column(db.Integer, default=0)
    drawn = db.Column(db.Integer, default=0)
    lost = db.Column(db.Integer, default=0)
    
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    goal_diff = db.Column(db.Integer, default=0)
    
    points = db.Column(db.Integer, default=0)
