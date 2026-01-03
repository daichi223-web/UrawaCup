import os
from flask import Flask, render_template
from database import db
from models import Team, Match, Standing

def create_app():
    app = Flask(__name__)
    
    # Configure Database
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'urawacup.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)

    # Register Routes
    from flask import request, redirect, url_for, flash

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/teams', methods=['GET', 'POST'])
    def teams_route():
        if request.method == 'POST':
            name = request.form.get('name')
            group = request.form.get('group')
            is_local = True if request.form.get('is_local') else False
            
            if name and group:
                new_team = Team(name=name, group=group, is_local=is_local)
                db.session.add(new_team)
                db.session.commit()
                
                # Initialize Standing for the new team
                new_standing = Standing(team_id=new_team.id)
                db.session.add(new_standing)
                db.session.commit()
                
                flash('Team added successfully!', 'success')
            else:
                flash('Name and Group are required.', 'danger')
            return redirect(url_for('teams_route'))

        teams = Team.query.all()
        return render_template('teams.html', teams=teams)

    @app.route('/matches')
    def matches_route():
        matches = Match.query.order_by(Match.day, Match.group).all()
        teams = Team.query.order_by(Team.group, Team.name).all()
        return render_template('matches.html', matches=matches, teams=teams)

    @app.route('/matches/add', methods=['POST'])
    def add_match():
        day = request.form.get('day')
        group = request.form.get('group')
        home_id = request.form.get('home_team_id')
        away_id = request.form.get('away_team_id')
        
        if home_id == away_id:
             flash('Home and Away teams must be different.', 'danger')
             return redirect(url_for('matches_route'))

        new_match = Match(day=day, group=group, home_team_id=home_id, away_team_id=away_id)
        db.session.add(new_match)
        db.session.commit()
        flash('Match scheduled.', 'success')
        return redirect(url_for('matches_route'))

    @app.route('/matches/update', methods=['POST'])
    def update_match():
        match_id = request.form.get('match_id')
        home_score = request.form.get('home_score')
        away_score = request.form.get('away_score')
        
        match = Match.query.get(match_id)
        if match and home_score is not None and away_score is not None:
            if home_score == '' or away_score == '':
                 # Clear score functionality if needed, for now ignore empty submission if intended to clear
                 pass 
            else:
                match.home_score = int(home_score)
                match.away_score = int(away_score)
                match.is_finished = True
                db.session.commit()
                recalculate_standings()
                flash('Score updated and standings calculated.', 'success')
        
        return redirect(url_for('matches_route'))

    @app.route('/standings')
    def standings_route():
        # Get all standings, organize by group
        groups = ['A', 'B', 'C', 'D']
        standings_data = {}
        for g in groups:
            # Sort by Points DESC, Goal Diff DESC, Goals For DESC
            st = Standing.query.join(Team).filter(Team.group == g).order_by(
                Standing.points.desc(), 
                Standing.goal_diff.desc(), 
                Standing.goals_for.desc()
            ).all()
            standings_data[g] = st
            
        return render_template('standings.html', standings=standings_data)

    def recalculate_standings():
        # Reset all standings
        standings = Standing.query.all()
        for st in standings:
            st.played = 0
            st.won = 0
            st.drawn = 0
            st.lost = 0
            st.goals_for = 0
            st.goals_against = 0
            st.goal_diff = 0
            st.points = 0
        
        # Re-process all finished matches
        matches = Match.query.filter_by(is_finished=True).all()
        for m in matches:
            home_st = Standing.query.filter_by(team_id=m.home_team_id).first()
            away_st = Standing.query.filter_by(team_id=m.away_team_id).first()
            
            if not home_st or not away_st: continue

            home_st.played += 1
            away_st.played += 1
            
            home_st.goals_for += m.home_score
            home_st.goals_against += m.away_score
            home_st.goal_diff = home_st.goals_for - home_st.goals_against
            
            away_st.goals_for += m.away_score
            away_st.goals_against += m.home_score
            away_st.goal_diff = away_st.goals_for - away_st.goals_against
            
            if m.home_score > m.away_score:
                home_st.won += 1
                home_st.points += 3
                away_st.lost += 1
            elif m.home_score < m.away_score:
                away_st.won += 1
                away_st.points += 3
                home_st.lost += 1
            else:
                home_st.drawn += 1
                home_st.points += 1
                away_st.drawn += 1
                away_st.points += 1
        
        db.session.commit()

    @app.route('/export/matches')
    def export_matches():
        import csv
        import io
        from flask import make_response

        matches = Match.query.order_by(Match.day, Match.group).all()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Match ID', 'Day', 'Group', 'Home Team', 'Home Score', 'Away Score', 'Away Team', 'Status'])
        
        for m in matches:
            status = 'Finished' if m.is_finished else 'Scheduled'
            cw.writerow([
                m.id, 
                m.day, 
                m.group if m.group else 'Finals',
                m.home_team.name,
                m.home_score,
                m.away_score,
                m.away_team.name,
                status
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=matches_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
