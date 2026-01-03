import sys
sys.path.insert(0, "D:/UrawaCup/src/backend")

from database import SessionLocal
from models.standing import Standing
from models.group import Group
from schemas.group import GroupResponse
from sqlalchemy.orm import joinedload

db = SessionLocal()

try:
    # Get groups
    groups = db.query(Group).filter(Group.tournament_id == 1).order_by(Group.id).all()
    print(f"Found {len(groups)} groups")

    for group in groups:
        print(f"\nGroup: {group.id}, tournament_id={group.tournament_id}, name={group.name}")

        # Try to convert to Pydantic model
        try:
            group_response = GroupResponse.model_validate(group)
            print(f"  GroupResponse: {group_response}")
        except Exception as e:
            print(f"  Error converting to GroupResponse: {e}")

        # Get standings for this group
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
        print(f"  Standings count: {len(standings)}")

finally:
    db.close()
