# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import db_manager # Import the separated database logic
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()
app.secret_key = os.envion.get('FLASK_SECRET_KEY') 

# --- FLASK ROUTES ---

@app.route('/')
def index():
    """Main dashboard showing all tournaments and options."""
    tournaments = db_manager.get_all_tournaments()
    return render_template('index.html', tournaments=tournaments)

# --- CREATE Tournament ---
@app.route('/createtournament', methods=['GET', 'POST'])
def new_tourn_route():
    """Route for creating a new tournament."""
    if request.method == 'POST':
        name = request.form['name']
        status = request.form['status']
        type_str = request.form['type']
        
        if name and status and type_str in ['solo', 'teamed']:
            db_manager.new_tournament(name, status, type_str)
            flash(f'Tournament "{name}" created successfully!', 'success')
        else:
            flash('Invalid input for new tournament.', 'error')
            
        return redirect(url_for('index'))
    return render_template('new_tournament.html')

# --- READ Standings ---
@app.route('/standings/<tourn_id>')
def standings_route(tourn_id):
    """Route for displaying tournament standings."""
    tourn_name, standings = db_manager.get_standings(tourn_id)
    for t in standings : team_id = t['id']
    if tourn_name == "Tournament not found":
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        return redirect(url_for('index'))
        
    return render_template('standings.html', 
                           tourn_name=tourn_name, 
                           tourn_id=tourn_id,
                           standings=standings,
                           )

@app.route('/teams/<tourn_id>')
def view_team(tourn_id):
    tourn_name, info = db_manager.team_info(tourn_id)
    if tourn_name == "Tournament not found":
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        return redirect(url_for('index'))

    return render_template('view_team.html',
                           tourn_id = tourn_id,
                           tourn_name = tourn_name,
                           info = info)

@app.route('/teams/<tourn_id>/<team_id>/edit', methods=['POST','GET'])
def edit_team(tourn_id,team_id):
    tourn_name, info = db_manager.team_info(tourn_id)
    data = db_manager.get_team_by_id(team_id,tourn_id)
    
    if tourn_name == "Tournament not found":
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            data = {'name':request.form['name'],'score':int(request.form['score'])}
            print(data)
            db_manager.editteam(team_id,tourn_id,data=data)
        except:
            flash('Invalid input for new tournament.', 'error')
            
        return redirect(url_for('view_team',tourn_id = tourn_id))
    return render_template('edit_team.html',
                           tourn_id = tourn_id,
                           tourn_name = tourn_name,
                           data = data
                           )

# --- UPDATE Tournament ---
@app.route('/update/<tourn_id>', methods=['GET', 'POST'])
def update_tourn_route(tourn_id):
    """Route for updating an existing tournament."""
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    
    if not tourn_data:
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        new_data = {}
        new_name = request.form['name']
        new_status = request.form['status']
        
        if new_name and new_name != tourn_data.get('name'):
            new_data['name'] = new_name
        if new_status and new_status != tourn_data.get('status'):
            new_data['status'] = new_status
            
        if new_data:
            db_manager.update_tournament(tourn_id, new_data)
            flash(f'Tournament "{new_name or tourn_data["name"]}" updated successfully!', 'success')
        else:
            flash('No changes detected for update.', 'info')
            
        return redirect(url_for('index'))
        
    return render_template('update_tournament.html', tournament=tourn_data)

@app.route('/delete/<tourn_id>/<team_id>', methods=['POST'])
def del_team(team_id,tourn_id):
    
    db_manager.delteam(team_id,tourn_id)
    return redirect(url_for('view_team',tourn_id=tourn_id))    

# --- DELETE Tournament ---
@app.route('/delete/<tourn_id>', methods=['POST'])
def delete_tourn_route(tourn_id):
    """Deletes a tournament."""
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if tourn_data:
        db_manager.delete_tournament(tourn_id)
        flash(f'Tournament "{tourn_data["name"]}" deleted successfully.', 'success')
    else:
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        
    return redirect(url_for('index'))

# --- CREATE Team ---
@app.route('/add_team/<tourn_id>', methods=['GET', 'POST'])
def add_team_route(tourn_id):
    """Route for adding a team to a tournament."""
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data or tourn_data.get('type') != 'teamed':
        flash('Tournament not found or is not a "teamed" tournament.', 'error')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form['name']
        try:
            iniscore = int(request.form['score'])
        except ValueError:
            iniscore = 0
            
        db_manager.add_team_to_tournament(tourn_id, name, iniscore)
        flash(f'Team "{name}" added to {tourn_data["name"]}.', 'success')
        return redirect(url_for('add_team_route', tourn_id=tourn_id))
    
    return render_template('add_team.html', tournament=tourn_data)


if __name__ == '__main__':
    app.run(debug=True)