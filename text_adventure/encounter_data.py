"""Read story/encounters.json."""
import json
from functools import lru_cache
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/"story"/"encounters.json"
@lru_cache(maxsize=1)
def load():
    return json.loads(PATH.read_text(encoding="utf-8"))
def encounter(eid):
    return load()["data_encounters"][eid]
def additions(scene_id):
    return load()["scenes"][scene_id].get("after_scene",[])
