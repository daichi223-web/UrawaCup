
import httpx
import time

API_URL = "http://localhost:8100/api"

def verify_player_linkage():
    client = httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)
    
    # 1. Login as Admin
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin1234"})
    if resp.status_code != 200:
        print(f"Login Failed: {resp.status_code}")
        return
    # Handle both snake_case and camelCase token keys
    data = resp.json()
    token = data.get("accessToken") or data.get("access_token")
    if not token:
        print(f"Login Response: {data}")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 2. Setup: Get a Tournament and Team
        print("Getting tournaments...")
        resp = client.get("/tournaments", headers=headers)
        print(f"Tournaments: {resp.status_code}")
        if resp.status_code != 200:
             print(resp.text)
        tournament_id = resp.json()["tournaments"][0]["id"]
        
        print("Getting teams...")
        resp = client.get(f"/teams?tournament_id={tournament_id}", headers=headers)
        teams = resp.json()["teams"]
        team = teams[0]
        team_id = team["id"]
        
        print(f"Target Team: {team['name']} (ID: {team_id})")
        
        # 3. Create a Player linked to this team
        player_data = {
            "name": "Test Striker",
            "number": 10,
            "position": "FW",
            "team_id": team_id
        }
        print("Creating player...")
        # Note: According to routes/players.py, route is POST /players/ (prefix /players, path /)
        resp = client.post("/players/", json=player_data, headers=headers) 
        print(f"Create Player Status: {resp.status_code}")
        
        player_id = None
        if resp.status_code in [200, 201]:
            player_id = resp.json()["id"]
            print(f"Created Player: {player_id}")
        else:
            print(f"Failed to create player: {resp.status_code} {resp.text}")
            return

        # 4. Create a Match (or find one)
        print("Finding match...")
        resp = client.get(f"/matches?tournament_id={tournament_id}&limit=100", headers=headers)
        matches = resp.json()["matches"]
        target_match = None
        for m in matches:
            # Check if match is FINISHED or SCHEDULED. If scheduled, we can finish it.
            if m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id:
                target_match = m
                break
        
        if not target_match:
            print("No match found for team.")
            return

        match_id = target_match["id"]
        print(f"Target Match: {match_id}")

        # 5. Input Score with Goal linked to Player
        is_home = (target_match["homeTeam"]["id"] == team_id)
        
        score_data = {
            "homeScoreHalf1": 1 if is_home else 0,
            "homeScoreHalf2": 0,
            "awayScoreHalf1": 0 if is_home else 1,
            "awayScoreHalf2": 0,
            "status": "finished",
            "goals": [
                {
                    "minute": 15,
                    "half": 1,
                    "teamId": team_id,
                    "playerId": player_id,  # LINKAGE HERE
                    "playerName": "Test Striker",
                    "isOwnGoal": False,
                    "isPenalty": False
                }
            ]
        }
        
        print("Updating score...")
        resp = client.put(f"/matches/{match_id}/score", json=score_data, headers=headers)
        if resp.status_code == 200:
            print("Score verification updated.")
        else:
            print(f"Failed to update score: {resp.status_code} {resp.text}")
            return

        # 6. Verify Scorer Ranking
        print("Verifying ranking...")
        resp = client.get(f"/standings/top-scorers?tournament_id={tournament_id}", headers=headers)
        print(f"Ranking Status: {resp.status_code}")
        if resp.status_code != 200:
             print(resp.text)
             
        scorers = resp.json()
        
        found = False
        for s in scorers:
            if s["team_id"] == team_id and s["player_name"] == "Test Striker":
                 # Note: Scorer response has 'team_id' and 'player_name', maybe doesn't return 'player_id'?
                 # Checked standings.py: returns player_name, team_id, team_name, goals. NO player_id.
                print(f"SUCCESS: Player {s['player_name']} found in ranking with {s['goals']} goals.")
                found = True
                break
        
        if not found:
            print("FAILURE: Player not found in scorer ranking.")
            print(scorers)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_player_linkage()
