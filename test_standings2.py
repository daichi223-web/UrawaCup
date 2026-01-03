import sys
sys.path.insert(0, "D:/UrawaCup/src/backend")

from database import SessionLocal
from models.standing import Standing
from models.group import Group
from schemas.group import GroupResponse
from schemas.standing import GroupStanding, StandingWithTeam
from sqlalchemy.orm import joinedload

db = SessionLocal()

try:
    # Get groups
    groups = db.query(Group).filter(Group.tournament_id == 1).order_by(Group.id).all()

    result = []
    for group in groups:
        standings = (
            db.query(Standing)
            .options(joinedload(Standing.team))
            .filter(
                Standing.tournament_id == 1,
                Standing.group_id == group.id,
            )
            .order_by(Standing.rank)
            .all()
        )

        # Try to create GroupStanding
        try:
            group_standing = GroupStanding(
                group=GroupResponse.model_validate(group),
                standings=standings,
            )
            result.append(group_standing)
            print(f"Group {group.id}: OK ({len(standings)} standings)")
        except Exception as e:
            print(f"Group {group.id}: ERROR - {e}")
            import traceback
            traceback.print_exc()

    print(f"\nTotal groups: {len(result)}")

    # Test JSON serialization
    import json
    for gs in result:
        try:
            json_data = gs.model_dump_json()
            print(f"Group {gs.group.id} JSON OK (length: {len(json_data)})")
        except Exception as e:
            print(f"Group {gs.group.id} JSON ERROR: {e}")

finally:
    db.close()
