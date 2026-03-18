import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()
# --- FIREBASE SETUP ---
try:
    firebase_admin.initialize_app()
    db = firestore.client()
    tref = db.collection('tournament')
    print(" + Firebase initialized successfully in db_manager.")
except Exception as e:
    print(f" + Error initializing Firebase: {e}")
    db = None
    tref = None

# --- CORE DB FUNCTIONS --- 

def get_all_tournaments():
    """Fetches all tournaments with their ID, name, status, and type."""
    if tref is None: return []
    tlist_data = []
    for doc in tref.stream():
        data = doc.to_dict()
        tlist_data.append({
            'id': doc.id,
            'name': data.get('name', 'Unnamed Tournament'),
            'type': data.get('type', 'solo'),
            'status': data.get('status', 'Open'),
            'reg_time': data.get('reg-time', 'N/A')
        })
    return tlist_data

def get_tournament_by_id(tourn_id):
    """
    Fetches a single tournament document by ID.

    # Parameters:
    tourn_id (str): The ID of the tournament to fetch.
    """
    if tref is None: return None
    doc = tref.document(tourn_id).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    # Change: return this dict so app.py doesn't break
    return {'name': "Tournament not found", 'type': 'solo'}

def get_tournament_current_round(tourn_id):
    """
    Fetches the current round of a tournament by ID.

    # Parameters:
    tourn_id (str): The ID of the tournament to fetch.

    # Returns:
    int: The current round of the tournament. Returns None if the tournament does not exist.
    """
    if tref is None: return None
    doc = tref.document(tourn_id).get()
    if doc.exists:
        data = doc.to_dict()

    return data['current_round']

def new_tournament(name, status, type_str, strict, default_bye):
    """
    Creates a new tournament document in the Firestore database.

    # Parameters:
    name (str): The name of the tournament.
    status (str): The status of the tournament (Open, Closed, etc.).
    type_str (str): The type of tournament (solo or teamed).
    strict (bool): Whether the Swiss system is strict for this tournament.
    default_bye (int): The points awarded for BYE in this tournament.

    # Returns:
    None
    """
    if tref is None: return
    info = {
        'name': name,
        'status': status,
        'type': type_str,
        'strict': strict, 
        'current_round': 0,
        'defualt_bye' : default_bye,
        'time_created' : firestore.firestore.SERVER_TIMESTAMP
    }
    tref.add(info)

def update_tournament(tourn_id, new_data):
    """Updates fields of an existing tournament."""
    if tref is None: return
    if new_data:
        tref.document(tourn_id).update(new_data)

def delete_tournament(tourn_id):
    """Deletes a tournament document."""
    if tref is None: return
    tref.document(tourn_id).delete()

def add_team_to_tournament(tourn_id, data=dict):
    """Adds a new team to a 'teamed' tournament."""
    if tref is None: return
    tref.document(tourn_id).collection('teams').add(data)

def get_teams_for_tournament(tourn_id):
    """Gets all teams for a teamed tournament."""
    if tref is None: return []
    teams_list = []
    teams_ref = tref.document(tourn_id).collection('teams')
    for doc in teams_ref.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        teams_list.append(data)
    return teams_list

def get_team_by_id(team_id,tourn_id):
    """Fetches a single tournament document."""
    if tref is None: return None
    doc = tref.document(tourn_id).collection('teams').document(team_id).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        
        return data
        
    return None


def get_standings(tourn_id):
    """Calculates and returns sorted standings (players or teams)."""
    tourn_data = get_tournament_by_id(tourn_id)
    if not tourn_data:
        return "Tournament not found", []

    tourn_name = tourn_data.get('name', 'Unnamed Tournament')
    tourn_type = tourn_data.get('type', 'solo')
    
    standings = []
    
    if tourn_type == 'solo':
        # Get players
        players_ref = tref.document(tourn_id).collection('players')
        for doc in players_ref.stream():
            data = doc.to_dict()
            standings.append({
                'name': data.get('name', 'N/A Player'), 
                'score': data.get('score', 0), 
                'id': doc.id
            })
            
    elif tourn_type == 'teamed':
        # Get teams
        teams_ref = tref.document(tourn_id).collection('teams')
        for doc in teams_ref.stream():
            data = doc.to_dict()
            standings.append({
                'name': data.get('name', 'N/A Team'), 
                'score': data.get('score', 0), 
                'id' : doc.id
            })
        
    # Sort the results by score (descending)
    standings.sort(key=lambda x: x['score'], reverse=True)
    
    return tourn_name, standings

def team_info(tourn_id):
    tourn_data = get_tournament_by_id(tourn_id)
    if not tourn_data:
        return "Tournament not found", []

    tourn_name = tourn_data.get('name', 'Unnamed Tournament')
    tourn_type = tourn_data.get('type', 'solo')
    
    info = []

    if tourn_type == 'teamed':
        # Get teams
        teams_ref = tref.document(tourn_id).collection('teams')
        for doc in teams_ref.stream():
            data = doc.to_dict()
            info.append({
                'name': data.get('name', 'N/A Team'), 
                'score': data.get('score', 0),
                'id' : doc.id
            })
        
    # Sort the results by score (descending)
    
    return tourn_name, info

def delteam(team_id,tourn_id):
    tref.document(tourn_id).collection('teams').document(team_id).delete()

def editteam(team_id,tourn_id,data):
    tref.document(tourn_id).collection('teams').document(team_id).update(data)



def addplayer(tourn_id,data):
    tref.document(tourn_id).collection('players').add(data)

def editplayer(player_id,tourn_id,data):
    tref.document(tourn_id).collection('players').document(player_id).update(data)

def delplayer(player_id,tourn_id):
    tref.document(tourn_id).collection('players').document(player_id).delete()

def player_info(tourn_id):
    tourn_data = get_tournament_by_id(tourn_id)
    if not tourn_data or tourn_data.get('name') == "Tournament not found":
        return "Tournament not found", []

    tourn_name = tourn_data.get('name', 'Unnamed Tournament')
    
    info = []
    # Make sure you are pulling from 'players' collection
    players_ref = tref.document(tourn_id).collection('players')
    for doc in players_ref.stream():
        data = doc.to_dict()
        info.append({
            'firstname': data.get('firstname', 'N/A Player'),
            'lastname': data.get('lastname', 'N/A Player'), # Fixed label
            'name' : data.get('name', 'N/A Player'),
            'score': data.get('score', 0),
            'id' : doc.id
        })
    return tourn_name, info

def get_player_by_id(player_id,tourn_id):
    if tref is None: return None
    doc = tref.document(tourn_id).collection('players').document(player_id).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        
        return data
        
    return None

def get_players_alphabetical(tourn_id):
    players_ref = tref.document(tourn_id).collection('players')
    players = []
    for doc in players_ref.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        players.append(data)
    return sorted(players, key=lambda x: x['name'])


def save_pairings(tourn_id, round_number, pairs, bye, isactive):
    round_info = {'round_number':round_number,'isactive': isactive,'pairs':pairs, 'bye_pair':bye}
    tref.document(tourn_id).collection('rounds').document(f'{round_number}').set(round_info)
    

def get_round_info(tourn_id):
    rounds_list = []
    rounds = tref.document(tourn_id).collection('rounds')
    for round in rounds.stream():
        info = round.to_dict()
        info['id'] = round.id
        info['round_number'] = info.get('round_number', 1)
        rounds_list.append(info)
        
    rounds_list = sorted(rounds_list, key=lambda x:x['round_number'], reverse=True)
    return rounds_list

