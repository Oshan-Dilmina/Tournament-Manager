import random
import db_manager


class SoloPair:
    def __init__(self, tourn_id, current_round):
        self.tourn_id = tourn_id
        self.current_round = current_round

    def pair(self):
        
        _, players = db_manager.player_info(self.tourn_id)
        tourn = db_manager.get_tournament_by_id(self.tourn_id)

        if tourn.get("status") == "over":
            return "Tournament is over", 400

        if len(players) < 2:
            return "Not enough players", 400

        
        for p in players:
            p.setdefault("op", [])
            p.setdefault("byes", 0)
            p.setdefault("last_bye_round", 0)

        
        brackets = {}
        for p in players:
            brackets.setdefault(p["score"], []).append(p)

        ordered = []
        for score in sorted(brackets.keys(), reverse=True):
            random.shuffle(brackets[score])
            ordered.extend(brackets[score])

        unpaired = ordered[:]
        pairings = []
        table = 1

        
        if len(unpaired) % 2 == 1:
            players_ref = db_manager.tref.document(self.tourn_id).collection('players')
            for p in unpaired:
                newdata = players_ref.document(p['id']).get().to_dict()
                p["byes"] = newdata.get('byes',0)
                p["last_bye_round"] = newdata.get('last_bye_round',0)
                p["op"] = newdata.get('op',[])
                print(p['byes'])
                min_byes = min(p["byes"] for p in unpaired)
                candidates = [p for p in unpaired if p["byes"] == min_byes]

            
            non_consecutive = [
                p for p in candidates
                if p["last_bye_round"] != self.current_round - 1
            ]

            if non_consecutive:
                print(non_consecutive)
                candidates = non_consecutive
            

            
            bye_player = min(candidates, key=lambda p: p["score"])
            unpaired.remove(bye_player)

            

            
            players_ref.document(bye_player["id"]).update({
                "byes": db_manager.firestore.Increment(1),
                "last_bye_round": self.current_round
            })

            
            refreshed = players_ref.document(bye_player["id"]).get().to_dict()
            bye_player.update(refreshed)

            bye_pair = {
                "p1": bye_player,
                "p2": "BYE",
                "table": None
            }

        
        while unpaired:
            p1 = unpaired.pop(0)
            p2 = None

            
            p1['op'] = players_ref.document(p1["id"]).get().to_dict()['op']
            
            for i, candidate in enumerate(unpaired):
                if candidate["id"] not in p1["op"]:
                    p2 = unpaired.pop(i)
                    break

            
            if p2 is None and unpaired:
                p2 = unpaired.pop(0)

            p2['op'] = players_ref.document(p2["id"]).get().to_dict()['op']

            pairings.append({
                "p1": p1,
                "p2": p2,
                "table": table
            })
            table += 1

            if p2:
                
                p1["op"].append(p2["id"])
                p2["op"].append(p1["id"])

                
                db_manager.editplayer(
                    p1["id"], self.tourn_id,
                    {"op": db_manager.firestore.ArrayUnion([p2["id"]])}
                )
                db_manager.editplayer(
                    p2["id"], self.tourn_id,
                    {"op": db_manager.firestore.ArrayUnion([p1["id"]])}
                )

        
        db_manager.update_tournament(
            self.tourn_id,
            {"round_count": self.current_round}
        )
        
        db_manager.save_pairings(self.tourn_id,self.current_round,pairings,bye_pair,True)



class TeamPair:
    def __init__(self, tourn_id, current_round):
        self.tourn_id = tourn_id
        self.current_round = current_round

    def pair(self):
        
        _, teams = db_manager.team_info(self.tourn_id)
        tourn = db_manager.get_tournament_by_id(self.tourn_id)

        if tourn.get("status") == "over":
            return "Tournament is over", 400

        if len(teams) < 2:
            return "Not enough teams", 400

        
        for t in teams:
            t.setdefault("op", [])
            t.setdefault("byes", 0)
            t.setdefault("last_bye_round", 0)

        
        brackets = {}
        for t in teams:
            brackets.setdefault(t["score"], []).append(t)

        ordered = []
        for score in sorted(brackets.keys(), reverse=True):
            random.shuffle(brackets[score])
            ordered.extend(brackets[score])

        unpaired = ordered[:]
        pairings = []
        table = 1

        
        if len(unpaired) % 2 == 1:
            teams_ref = db_manager.tref.document(self.tourn_id).collection('teams')
            for t in unpaired:
                newdata = teams_ref.document(t['id']).get().to_dict()
                t["byes"] = newdata.get('byes',0)
                t["last_bye_round"] = newdata.get('last_bye_round',0)
                t["op"] = newdata.get('op',[])
                print(t['byes'])
                min_byes = min(t["byes"] for t in unpaired)
                candidates = [t for t in unpaired if t["byes"] == min_byes]

            
            non_consecutive = [
                t for t in candidates
                if t["last_bye_round"] != self.current_round - 1
            ]

            if non_consecutive:
                print(non_consecutive)
                candidates = non_consecutive
            

            
            bye_team = min(candidates, key=lambda t: t["score"])
            unpaired.remove(bye_team)

            

            
            teams_ref.document(bye_team["id"]).update({
                "byes": db_manager.firestore.Increment(1),
                "last_bye_round": self.current_round
            })

            
            refreshed = teams_ref.document(bye_team["id"]).get().to_dict()
            bye_team.update(refreshed)

            bye_pair = {
                "t1": bye_team,
                "t2": "BYE",
                "table": None
            }
        else:
            bye_pair = None
        
        while unpaired:
            t1 = unpaired.pop(0)
            t2 = None
            teams_ref = db_manager.tref.document(self.tourn_id).collection('teams')

            t1['op'] = teams_ref.document(t1["id"]).get().to_dict()['op']
            
            for i, candidate in enumerate(unpaired):
                if candidate["id"] not in t1["op"]:
                    t2 = unpaired.pop(i)
                    break

            
            if t2 is None and unpaired:
                t2 = unpaired.pop(0)

            t2['op'] = teams_ref.document(t2["id"]).get().to_dict()['op']

            pairings.append({
                "t1": t1,
                "t2": t2,
                "table": table
            })
            table += 1

            if t2:
                
                t1["op"].append(t2["id"])
                t2["op"].append(t1["id"])

                db_manager.editteam(
                    t1["id"], self.tourn_id,
                    {"op": db_manager.firestore.ArrayUnion([t2["id"]])}
                )
                db_manager.editteam(
                    t2["id"], self.tourn_id,
                    {"op": db_manager.firestore.ArrayUnion([t1["id"]])}
                )

      
        db_manager.update_tournament(
            self.tourn_id,
            {"current_round": self.current_round}
        )
        db_manager.save_pairings(self.tourn_id,self.current_round,pairings,bye_pair,True)

        return pairings,bye_pair
