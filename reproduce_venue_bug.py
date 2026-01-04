
import sys
import os

# Add src/backend to path
sys.path.append(os.path.abspath("src/backend"))

from schemas.venue import VenueUpdate
from database import Base, SessionLocal
from models.venue import Venue

def test_venue_update():
    # ... (existing code omitted)
    pass

def test_pydantic_schema():
    print("\n--- Testing Pydantic Schema ---")
    data = {"forFinalDay": False, "isFinalsVenue": False}
    print(f"Input data: {data}")
    
    try:
        model = VenueUpdate(**data)
        print(f"Parsed model: {model}")
        print(f"dict(exclude_unset=True): {model.model_dump(exclude_unset=True)}")
        print(f"dict(by_alias=False, exclude_unset=True): {model.model_dump(by_alias=False, exclude_unset=True)}")
        
        dump = model.model_dump(by_alias=False, exclude_unset=True)
        if dump.get("for_final_day") is False:
             print("Schema parsing SUCCESS.")
        else:
             print("Schema parsing FAILED: for_final_day is missing or not False.")

    except Exception as e:
        print(f"Schema parsing ERROR: {e}")

if __name__ == "__main__":
    test_pydantic_schema()
