from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, make_response
import db_manager
import os
from dotenv import load_dotenv
from forms import *
import pair
from auth import auth_bp, login_required, session
from werkzeug.security import generate_password_hash
import csv
from io import StringIO


app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get('FLASK_SECRET_KEY') 
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    tournaments = db_manager.get_all_tournaments()
    return render_template('index.html', tournaments=tournaments)

@app.route('/dashboard')
@login_required
def dashboard():
    tournaments = db_manager.get_all_tournaments()
    return render_template('dashboard.html', tournaments=tournaments)

@app.route('/tournament/<tourn_id>/round/<int:current_round>/export_csv')
def export_csv(tourn_id, current_round):
    data = db_manager.get_round_pairings(tourn_id, current_round)
    if not data:
        return "Round not found", 404

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Table', 'Team 1', 'Score 1', 'Score 2', 'Team 2'])

    # pairs is a list, match is each dictionary inside that list
    for idx, match in enumerate(data['pairs']):
        # Using .get() safely to find the names
        t1_name = match.get('t1', {}).get('name', 'N/A')
        t2_data = match.get('t2')
        
        # Handle t2 if it exists, otherwise it's a BYE
        t2_name = t2_data.get('name', 'BYE') if isinstance(t2_data, dict) else 'BYE'

        cw.writerow([f"Table {idx + 1}", t1_name, '', '', t2_name])

    # Check for the separate bye_pair field if applicable
    if data.get('bye_pair'):
        bye_name = data['bye_pair'].get('name', 'N/A')
        cw.writerow(['BYE', bye_name, '', '', '---'])

    output = make_response(si.getvalue())
    filename = f"{data['tourn_name']}_Round_{current_round}.csv".replace(" ", "_")
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output
#----------------------------------CREATES--------------------------------------------------------------
@app.route('/tournament/create', methods=['GET', 'POST'])
@login_required
def new_tourn_route():
    if request.method == 'POST':
        name = request.form.get('name')
        status = request.form.get('status')
        type_str = request.form.get('type')
        strict = request.form.get('strict')
        default_bye = request.form.get('margin_bye_points')
        record_player = request.form.get('record_player')
    

        if name and status and type_str in ['solo', 'teamed']:
            db_manager.new_tournament(name, status, type_str, strict, int(default_bye or 0), record_player)
            flash(f'Tournament "{name}" created successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            abort(400, description="Invalid input fields for new tournament.")
            
    return render_template('new_tournament.html')

@app.route('/tournament/<tourn_id>/teams/new', methods=['POST'])
@login_required
def add_team_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exist')
         
    addteamform = AddTeamForm()
    if addteamform.validate_on_submit():
        try:
            data = {
                'name': addteamform.name.data, 
                'score': addteamform.score.data, 
                'reg-time': db_manager.firestore.firestore.SERVER_TIMESTAMP, 
                'byes': 0, 
                'last_bye_round': 0, 
                'op': []
            }
            db_manager.add_team_to_tournament(tourn_id, data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': f'DB Error: {str(e)}'}), 500
    else:
        abort(400, description=addteamform.errors)

@app.route('/tournament/<tourn_id>/teams/new/modal', methods=['GET'])
@login_required
def getnewteam(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exist')

    form = AddTeamForm()
    return render_template('add_team_modal.html', tourn_id=tourn_id, tourn_data=tourn_data, form=form)

@app.route('/tournament/<tourn_id>/players/new', methods=['POST'])
@login_required
def add_player_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description="Tournament not found.")


    addplayerform = AddPlayerForm()
    if addplayerform.validate_on_submit():
        try:
            data = {
                'name': f"{addplayerform.lastname.data},{addplayerform.firstname.data}",
                'firstname': addplayerform.firstname.data,
                'lastname': addplayerform.lastname.data, 
                'score': addplayerform.score.data, 
                'reg-time': db_manager.firestore.firestore.SERVER_TIMESTAMP, 
                'byes': 0, 
                'last_bye_round': 0, 
                'op': []
            }
            db_manager.addplayer(tourn_id, data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        abort(400, description=addplayerform.errors)

@app.route('/tournament/<tourn_id>/players/new/modal', methods=['GET'])
@login_required
def getnewplayer(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data: abort(404)

    form = AddPlayerForm()
    return render_template('add_player_modal.html', tourn_id=tourn_id, tourn_data=tourn_data, form=form)

@app.route('/admins/add', methods=['POST'])
@login_required
def add_admin_route():
    username = request.form.get('username').strip()
    password = request.form.get('password')

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for('admins'))

    # Check if admin already exists
    if db_manager.get_admin_password(username):
        flash("An admin with that username already exists.", "error")
    else:
        hashed_password = generate_password_hash(password)
        db_manager.save_admin_to_db(username, hashed_password)
        flash(f"New admin '{username}' added successfully!", "success")
    
    return redirect(url_for('admins'))

#--------------------------------------EDIT------------------------------------------------------------

@app.route('/tournament/<tourn_id>/players/<player_id>/edit/modal', methods=['GET'])
@login_required
def geteditplayer(tourn_id, player_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data: 
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exist')

    data = db_manager.get_player_by_id(player_id, tourn_id)
    if not data: 
        abort(404, description='Player you are looking for does not exist')
    
    # We use EditPlayerForm here (ensure this is in your forms.py)
    editplayerform = EditPlayerForm(data=data)
    
    # Using a dedicated edit_player_modal.html
    return render_template('edit_player_modal.html', 
                           tourn_id=tourn_id, 
                           tourn_name=tourn_data['name'], 
                           data=data, 
                           form=editplayerform)

@app.route('/tournament/<tourn_id>/players/<player_id>/edit', methods=['POST'])
@login_required
def edit_player(tourn_id, player_id):
    # ... previous checks ...
    editplayerform = EditPlayerForm()
    
    if editplayerform.validate_on_submit():
        newdata = {
            'firstname': editplayerform.firstname.data,
            'lastname': editplayerform.lastname.data,  # Make sure this is .lastname
            'name': f"{editplayerform.lastname.data},{editplayerform.firstname.data}",
            'score': editplayerform.score.data
        }
        db_manager.editplayer(player_id, tourn_id, newdata)
        return jsonify({'success': True})
    
    # If it fails, return the specific validation errors to debug
    return jsonify({'success': False, 'errors': editplayerform.errors}), 400
@app.route('/tournament/<tourn_id>/teams/<team_id>/edits', methods=['POST'])
@login_required
def edit_team(tourn_id, team_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    


    data = db_manager.get_team_by_id(team_id, tourn_id)
    editteamform = EditTeamForm(data=data)
    if editteamform.validate_on_submit():
        newdata = {'name': editteamform.name.data, 'score': editteamform.score.data}
        db_manager.editteam(team_id, tourn_id, newdata)
        return jsonify({'success': True})
    else:
        abort(400, description=editteamform.errors)

@app.route('/tournament/<tourn_id>/teams/<team_id>/edit/modal', methods=['GET'])
@login_required
def geteditteam(tourn_id, team_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data: 
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')


    data = db_manager.get_team_by_id(team_id, tourn_id)
    if not data: abort(404, description='Team you are looking for does not exsist')
    
    editteamform = EditTeamForm(data=data)
    return render_template('edit_team_modal.html', tourn_id=tourn_id, tourn_name=tourn_data['name'], data=data, form=editteamform)

@app.route('/tournament/<tourn_id>/update', methods=['GET', 'POST'])
@login_required
def update_tourn_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data: abort(404)
        
    if request.method == 'POST':
        new_data = {
            'name': request.form.get('name'),
            'status': request.form.get('status')
        }
        db_manager.update_tournament(tourn_id, new_data)
        flash('Tournament updated successfully!', 'success')
        return redirect(url_for('index'))
        
    return render_template('update_tournament.html', tournament=tourn_data)

#--------------------------------------DELETE------------------------------------------------------------

@app.route('/tournament/<tourn_id>/teams/<team_id>delete', methods=['POST'])
@login_required
def del_team(team_id, tourn_id):
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Team with ID "{team_id}" does not exsist')

    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        abort(403, description="You are not the creator of this tournament.")

    db_manager.delteam(team_id, tourn_id)
    return redirect(url_for('view_tournament', tourn_id=tourn_id))    

@app.route('/tournament/<tourn_id>/players/<player_id>/delete', methods=['POST'])
@login_required
def del_player(player_id, tourn_id):
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Player with ID "{player_id}" does not exsist')

    
    
    db_manager.delplayer(player_id, tourn_id)
    return redirect(url_for('view_tournament', tourn_id=tourn_id))    

@app.route('/tournament/<tourn_id>/delete', methods=['POST'])
@login_required
def delete_tourn_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    
    db_manager.delete_tournament(tourn_id)
    flash(f'Tournament deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/admins/delete/<username>', methods=['POST'])
@login_required
def delete_admin_route(username):
    # Prevent the current user from deleting themselves (safety first!)
    if username == session.get('user'):
        flash("You cannot delete your own account while logged in!", "error")
    else:
        db_manager.delete_admin(username)
        flash(f"Admin '{username}' removed.", "success")
    return redirect(url_for('admins'))

#--------------------------------------READ&PAIR------------------------------------------------------------

@app.route('/tournament/<tourn_id>')
def view_tournament(tourn_id):
    tourn = db_manager.get_tournament_by_id(tourn_id)
    
    if tourn['name'] == "Tournament not found":
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')

    if tourn['type'] == 'solo':
        tourn_name, info = db_manager.player_info(tourn_id)
        return render_template('view_tournament.html', tourn_id=tourn_id, tourn_name=tourn_name, tourn_type=tourn['type'], info=info)
    else:
        tourn_name, info = db_manager.team_info(tourn_id)
        return render_template('view_tournament.html', tourn_id=tourn_id, tourn_name=tourn_name, tourn_type=tourn['type'], info=info)

@app.route('/tournament/<tourn_id>/standings')
def standings_route(tourn_id):
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    tourn_name, standings = db_manager.get_standings(tourn_id)

    return render_template('standings.html', tourn_name=tourn_name, tourn_id=tourn_id, standings=standings)

@app.route('/tournament/<tourn_id>/pair')
@login_required
def pairing(tourn_id):
    tournament = db_manager.get_tournament_by_id(tourn_id)
    if not tournament:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    
        
    if tournament['status'] == 'over':
        abort(400, description="Tournament is already over.")
    
    if tournament['type'] == 'teamed' and len(db_manager.get_teams_for_tournament(tourn_id)) < 2:
        abort(400, description="Not enough Teams to start pairing.")
    elif tournament['type'] == 'solo' and len(db_manager.get_players_alphabetical(tourn_id)) < 2:
        abort(400, description="Not enough Players to start pairing.")
    
    current_round = db_manager.get_tournament_current_round(tourn_id) + 1
    default_bye = tournament['defualt_bye']
    rounds = db_manager.get_round_info(tourn_id)
    status = tournament['status']
    
    pairings = None
    bye_pair = None
    round_count = current_round
    active_round = next((r for r in rounds if r.get('isactive') is True), None)

    if active_round:
        pairings = active_round['pairs']
        bye_pair = active_round.get('bye_pair')
        round_count = active_round['round_number']
    else:
        if db_manager.get_tournament_by_id(tourn_id)['type'] == 'solo':
            pairings, bye_pair = pair.SoloPair(tourn_id, current_round).pair()
        elif db_manager.get_tournament_by_id(tourn_id)['type'] == 'teamed':
            pairings, bye_pair = pair.TeamPair(tourn_id, current_round).pair()
        else:
            abort(400, description="Bad Request")
        
    return render_template('pairings.html', 
                        pairings=pairings,
                        bye_pair=bye_pair, 
                        tourn_id=tourn_id, 
                        t_type=db_manager.get_tournament_by_id(tourn_id)['type'],
                        tourn_name=db_manager.get_tournament_by_id(tourn_id)['name'],
                        round_count=round_count,
                        defualt_bye=default_bye)

@app.route('/tournament/<tourn_id>/pair/<current_round>/submit', methods=['POST'])
@login_required
def submit_score(tourn_id, current_round):
    tourn = db_manager.get_tournament_by_id(tourn_id)
    if not tourn:
        abort(404)
    
    col_name = 'players' if tourn['type'] == 'solo' else 'teams'
    part_ref = db_manager.tref.document(tourn_id).collection(col_name)
    processed_ids = []

    for key in request.form:
        if key.startswith('score_'):
            p1_id = key.replace('score_', '')
            
            # Skip if already handled or it's a BYE
            if p1_id in processed_ids or p1_id == "None" or p1_id == "BYE":
                continue

            p2_id = request.form.get(f'opp_{p1_id}')
            
            # Get scores, default to 0 if empty
            try:
                s1 = int(request.form.get(f'score_{p1_id}') or 0)
            except ValueError: s1 = 0

            # Logic for a real match
            if p2_id and p2_id != "BYE" and p2_id != "None":
                try:
                    s2 = int(request.form.get(f'score_{p2_id}') or 0)
                except ValueError: s2 = 0
                
                m1 = s1 - s2
                m2 = s2 - s1
                
                # Update P1
                part_ref.document(p1_id).update({"score": db_manager.firestore.Increment(m1)})
                # Update P2
                part_ref.document(p2_id).update({"score": db_manager.firestore.Increment(m2)})
                
                processed_ids.append(p2_id)
            
            # Logic for a BYE
            else:
                part_ref.document(p1_id).update({"score": db_manager.firestore.Increment(s1)})

            processed_ids.append(p1_id)

    # Deactivate the round
    db_manager.tref.document(tourn_id).collection('rounds').document(current_round).update({'isactive': False})
    
    flash(f"Round {current_round} results submitted successfully!")
    return redirect(url_for('view_tournament', tourn_id=tourn_id))

@app.route('/admins')
@login_required
def admins():
    admin_list = db_manager.get_all_admins()
    return render_template('admins.html', admins=admin_list)

#--------------------------------------ERROR------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e=e), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html', e=e), 400

@app.errorhandler(403)
@app.errorhandler(401)
def forbidden_unauthorized(e):
    return render_template('403.html',e=e,code=e.code), e.code

if __name__ == '__main__':
    app.run(debug=True)