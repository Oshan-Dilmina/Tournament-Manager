from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
import db_manager
import os
from dotenv import load_dotenv
from forms import *
import pair
from auth import auth_bp, login_required, session

app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get('FLASK_SECRET_KEY') 
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    tournaments = db_manager.get_all_tournaments()
    return render_template('index.html', tournaments=tournaments)


#----------------------------------CREATES--------------------------------------------------------------
@app.route('/tournament/create', methods=['GET', 'POST'])
@login_required
def new_tourn_route():
    if request.method == 'POST':
        name = request.form['name']
        status = request.form['status']
        type_str = request.form['type']
        strict = request.form['strict']
        default_bye = request.form['margin_bye_points']
        creator_email = session.get('user')
        
        bool_map = {"true": True, "false": False}
        strict = bool_map.get(strict.lower())

        if name and status and type_str in ['solo', 'teamed']:
            db_manager.new_tournament(name, status, type_str, strict, int(default_bye), creator_email)
            flash(f'Tournament "{name}" created successfully!', 'success')
        else:
            flash('Invalid input for new tournament.', 'error')
            
        return redirect(url_for('index'))
    return render_template('new_tournament.html')

@app.route('/tournament/<tourn_id>/teams/new', methods=['POST'])
@login_required
def add_team_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if tourn_data['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
        
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
        errors = {field: errors for field, errors in addteamform.errors.items()}
        abort(400, description=errors)
    
@app.route('/tournament/<tourn_id>/teams/new/modal', methods=['GET'])
@login_required
def getnewteam(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))

    form = AddTeamForm()
    return render_template('add_team_modal.html', tourn_id=tourn_id, tourn_data=tourn_data, form=form)

@app.route('/tournament/<tourn_id>/players/new', methods=['POST'])
@login_required
def add_player_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')

    if tourn_data.get('type') != 'solo':
        flash('Tournament not found or is not a "solo" tournament.', 'error')
        return redirect(url_for('index'))
    
    if tourn_data['creator_email'] != session.get('user'):
        return redirect(url_for('index'))

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
            return jsonify({'success': False, 'error': f'DB Error: {str(e)}'}), 500
    else:
        errors = {field: errors for field, errors in addplayerform.errors.items()}
        abort(400, description=errors)
    
@app.route('/tournament/<tourn_id>/players/new/modal', methods=['GET'])
@login_required
def getnewplayer(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if tourn_data['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    form = AddPlayerForm()
    return render_template('add_player_modal.html', tourn_id=tourn_id, tourn_data=tourn_data, form=form)


#--------------------------------------EDIT------------------------------------------------------------

@app.route('/tournament/<tourn_id>/teams/<team_id>/edits', methods=['POST'])
@login_required
def edit_team(tourn_id, team_id):
    tourn_name, info = db_manager.team_info(tourn_id)
    data = db_manager.get_team_by_id(team_id, tourn_id)
    
    if tourn_name == "Tournament not found":
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))

    editteamform = EditTeamForm(data=data)
    if editteamform.validate_on_submit():
        try:
            newdata = {'name': editteamform.name.data, 'score': editteamform.score.data}
            db_manager.editteam(team_id, tourn_id, newdata)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': f'DB Error: {str(e)}'}), 500
    else:
        errors = {field: errors for field, errors in editteamform.errors.items()}
        return jsonify({'success': False, 'errors': errors}), 400

@app.route('/tournament/<tourn_id>/teams/<team_id>/edit/modal', methods=['GET'])
@login_required
def geteditteam(tourn_id, team_id):
    tourn_name = db_manager.get_tournament_by_id(tourn_id)['name']

    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))

    data = db_manager.get_team_by_id(team_id, tourn_id)

    if not data:
        abort(404, description='Team you are looking for does not exsist')
    
    
    data['name'] = data['name'].strip()
    editteamform = EditTeamForm(data=data)

    return render_template('edit_team_modal.html', tourn_id=tourn_id, tourn_name=tourn_name, data=data, form=editteamform)

@app.route('/tournament/<tourn_id>/players/<player_id>/edit', methods=['POST'])
@login_required
def edit_player(tourn_id, player_id):
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Player with ID "{player_id}" does not exsist')

    form = EditPlayerForm()
    if form.validate_on_submit():
        newdata = {'name': form.name.data.strip(), 'score': form.score.data}
        db_manager.editplayer(player_id, tourn_id, newdata)
        return jsonify({'success': True})
    
    errors = {field: errs for field, errs in form.errors.items()}
    abort(400, description=errors)

@app.route('/tournament/<tourn_id>/players/<player_id>/edit/modal', methods=['GET'])
@login_required
def geteditplayer(tourn_id, player_id):
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    
    data = db_manager.get_player_by_id(player_id, tourn_id)
    if not data:
        abort(404, description='Player you are looking for does not exsist')
        
    form = EditPlayerForm(data=data)
    return render_template('edit_player_modal.html', tourn_id=tourn_id, data=data, form=form)

@app.route('/tournament/<tourn_id>/update', methods=['GET', 'POST'])
@login_required
def update_tourn_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    
    if not tourn_data:
        abort(404,description=f'Tournament with ID "{tourn_id}" does not exisit.')

    if tourn_data['creator_email'] != session.get('user'):
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


#--------------------------------------DELETE------------------------------------------------------------

@app.route('/tournament/<tourn_id>/teams/<team_id>delete', methods=['POST'])
@login_required
def del_team(team_id, tourn_id):
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Team with ID "{team_id}" does not exsist')
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    db_manager.delteam(team_id, tourn_id)
    return redirect(url_for('view_tournament', tourn_id=tourn_id))    

@app.route('/tournament/<tourn_id>/players/<player_id>/delete', methods=['POST'])
@login_required
def del_player(player_id, tourn_id):
    if not db_manager.get_tournament_by_id(tourn_id):
        abort(404, description=f'Player with ID "{player_id}" does not exsist')
    if db_manager.get_tournament_by_id(tourn_id)['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    db_manager.delplayer(player_id, tourn_id)
    return redirect(url_for('view_tournament', tourn_id=tourn_id))    

@app.route('/tournament/<tourn_id>/delete', methods=['POST'])
@login_required
def delete_tourn_route(tourn_id):
    tourn_data = db_manager.get_tournament_by_id(tourn_id)
    if not tourn_data:
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')

    if tourn_data['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    
    db_manager.delete_tournament(tourn_id)
    flash(f'Tournament "{tourn_data["name"]}" deleted successfully.', 'success')
    return redirect(url_for('index'))


#--------------------------------------READ&PAIR------------------------------------------------------------

@app.route('/tournament/<tourn_id>')
def view_tournament(tourn_id):
    tourn_type = db_manager.get_tournament_by_id(tourn_id)['type']
    tourn_name = db_manager.get_tournament_by_id(tourn_id)['name']
    if tourn_name == "Tournament not found":
        flash(f'Tournament ID {tourn_id} not found.', 'error')
        return redirect(url_for('index'))

    if tourn_type == 'solo':
        tourn_name, info = db_manager.player_info(tourn_id)
        return render_template('view_tournament.html', tourn_id=tourn_id, tourn_name=tourn_name, tourn_type=tourn_type, info=info)
    else:
        tourn_name, info = db_manager.team_info(tourn_id)
        return render_template('view_tournament.html', tourn_id=tourn_id, tourn_name=tourn_name, tourn_type=tourn_type, info=info)

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
    if tournament['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
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
        if db_manager.get_tournament_by_id(tourn_id)['type'] == 'solo' and status != 'over':
            pairings, bye_pair = pair.SoloPair(tourn_id, current_round).pair()
        elif db_manager.get_tournament_by_id(tourn_id)['type'] == 'teamed' and status != 'over':
            pairings, bye_pair = pair.TeamPair(tourn_id, current_round).pair()
        else:
            abort(400, description="Tournament is over")
        
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
    if not tourn(tourn_id):
        abort(404, description=f'Tournament with ID "{tourn_id}" does not exsist')
    if tourn['creator_email'] != session.get('user'):
        return redirect(url_for('index'))
    
    col_name = 'players' if tourn['type'] == 'solo' else 'teams'
    part_ref = db_manager.tref.document(tourn_id).collection(col_name)
    active_ref = db_manager.tref.document(tourn_id).collection('rounds').document(current_round)
    processed_ids = []

    for key in request.form:
        if key.startswith('score_'):
            p1_id = key.replace('score_', '')
            if p1_id in processed_ids or p1_id == "BYE":
                continue

            p2_id = request.form.get(f'opp_{p1_id}')
            s1 = int(request.form.get(f'score_{p1_id}', 0))

            if p2_id != "BYE":
                s2 = int(request.form.get(f'score_{p2_id}', 0))
                m1 = s1 - s2
                m2 = s2 - s1
                part_ref.document(p1_id).update({"score": db_manager.firestore.Increment(m1)})
                part_ref.document(p2_id).update({"score": db_manager.firestore.Increment(m2)})
                processed_ids.append(p2_id)
            else:
                part_ref.document(p1_id).update({"score": db_manager.firestore.Increment(s1)})

            processed_ids.append(p1_id)

    flash(f"Round {current_round} margins applied.")
    active_ref.update({'isactive': False})
    return redirect(url_for('index'))


#--------------------------------------ERROR------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e=e), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html', e=e), 400

@app.errorhandler(403)
def forbidden(e):
    return render_template('404.html',e=e)

if __name__ == '__main__':
    app.run(debug=True)