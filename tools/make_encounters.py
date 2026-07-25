#!/usr/bin/env python3
"""Replace the source dump with readable Realmbound encounter data."""
from __future__ import annotations
import ast, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'story'/'encounters.json'
STORY=ROOT/'text_adventure'/'story.py'
WEB=ROOT/'web'/'app.js'


def literal(node, default=None):
    try: return ast.literal_eval(node)
    except Exception: return default


def calls_in_order(fn):
    calls=[]
    for node in ast.walk(fn):
        if isinstance(node, ast.Call): calls.append(node)
    return sorted(calls,key=lambda n:(n.lineno,n.col_offset))


def build():
    from text_adventure.data import MONSTERS, LONG_ROAD_ENEMIES
    source=STORY.read_text(encoding='utf-8'); tree=ast.parse(source)
    order=[]; titles={}; functions={}
    for node in tree.body:
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            name=next((t.id for t in targets if isinstance(t,ast.Name)),None)
            value=node.value
            if name=='SCENE_ORDER': order=list(literal(value,[]))
            if name=='SCENE_TITLES' and isinstance(value,ast.Dict):
                for k,v in zip(value.keys,value.values):
                    if isinstance(k,ast.Constant) and isinstance(k.value,str) and isinstance(v,ast.Constant): titles[k.value]=v.value
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): functions[node.name]=node
    existing={}
    if OUT.exists():
        try: existing=json.loads(OUT.read_text(encoding='utf-8'))
        except Exception: existing={}
    existing_data=existing.get('data_encounters',{}) if isinstance(existing,dict) else {}
    scenes={}; data={k:v for k,v in existing_data.items() if isinstance(v,dict) and v.get('user_added')}
    for scene_id in order:
        fn=functions.get(scene_id+'_scene'); encounters=[]
        if fn:
            for call in calls_in_order(fn):
                name=''
                if isinstance(call.func,ast.Name): name=call.func.id
                elif isinstance(call.func,ast.Attribute): name=call.func.attr
                if name=='spell_fight' and call.args:
                    enemy=literal(call.args[0]);
                    if isinstance(enemy,str): encounters.append({'id':f'{scene_id}_{enemy.replace(" ","_")}_{call.lineno}','type':'battle','enemy':enemy,'runs_from':'custom_scene'})
                elif name=='_extra_fight' and len(call.args)>=4:
                    enemy,intro,run=map(literal,call.args[1:4])
                    if all(isinstance(x,str) for x in (enemy,intro,run)):
                        eid=f'{scene_id}_{enemy.replace(" ","_")}_{call.lineno}'
                        encounters.append({'id':eid,'type':'battle','enemy':enemy,'runs_from':'custom_scene'})
                        data[eid]={'id':eid,'name':enemy.title(),'scene':scene_id,'type':'battle','enemy':enemy,'intro':[intro],'choice':'fight_or_run','run':{'text':run,'game_over':True},'victory':{'rewards':[],'text':[],'offer_potions':True}}
                elif name=='run_shop': encounters.append({'id':f'{scene_id}_shop_{call.lineno}','type':'shop','runs_from':'custom_scene'})
                elif name=='_visit_church':
                    church=literal(call.args[1] if len(call.args)>1 else call.args[0],'Church')
                    encounters.append({'id':f'{scene_id}_rest_{call.lineno}','type':'rest','name':church,'runs_from':'custom_scene'})
                elif name in ('well_scene','clocktower_scene') and scene_id not in ('well','clocktower'):
                    encounters.append({'id':f'{scene_id}_{name}_{call.lineno}','type':'secret_route','destination':name.removesuffix('_scene'),'runs_from':'custom_scene'})
        previous=existing.get('scenes',{}).get(scene_id,{}) if isinstance(existing,dict) else {}
        scenes[scene_id]={'title':titles.get(scene_id,scene_id.replace('_',' ').title()),'summary':ast.get_docstring(fn) or '', 'encounters':encounters,'after_scene':previous.get('after_scene',[])}
    return {'schema_version':1,'game':'Realmbound','editing_help':{'add_encounter':['Copy or create an object in data_encounters.','Add its id to a scene after_scene list.','Python and HTML5 run that encounter automatically.'],'note':'runs_from custom_scene means special logic remains in code; this file still lists it so the story is easy to read.'},'scene_order':order,'scenes':scenes,'data_encounters':data,'monsters':MONSTERS,'sequences':{'hundred_day_road':{'enemies':list(LONG_ROAD_ENEMIES),'checkpoint_every':5,'rest_every':5,'shop_every':10}}}

LOADER='''"""Read story/encounters.json."""\nimport json\nfrom functools import lru_cache\nfrom pathlib import Path\nPATH=Path(__file__).resolve().parents[1]/"story"/"encounters.json"\n@lru_cache(maxsize=1)\ndef load():\n    return json.loads(PATH.read_text(encoding="utf-8"))\ndef encounter(eid):\n    return load()["data_encounters"][eid]\ndef additions(scene_id):\n    return load()["scenes"][scene_id].get("after_scene",[])\n'''

PYHELP='''def _run_json_encounter(encounter_id, player):\n    entry = encounter(encounter_id)\n    for line in entry.get("intro", []): say("\\n" + line, "beat")\n    if entry.get("type") == "battle":\n        if entry.get("choice") == "fight_or_run" and fight_or_run() == "run":\n            result = entry.get("run", {})\n            if result.get("text"): say("\\n" + result["text"], "beat")\n            if result.get("game_over"): game_over(player)\n            return\n        spell_fight(entry["enemy"], player)\n    for reward in entry.get("victory", {}).get("rewards", []):\n        if "item" in reward: player["backpack"].append(reward["item"])\n        if "money" in reward:\n            value=reward["money"]; amount=random.randint(value["min"],value["max"]) if isinstance(value,dict) else int(value); player["money"]+=amount\n    if entry.get("victory", {}).get("offer_potions"): offer_potions(player)\n'''

JSHELP='''    async runJsonEncounter(encounterId, player) {\n      const entry = ENCOUNTER_DATA.data_encounters[encounterId];\n      if (!entry) throw new Error(`Unknown encounter: ${encounterId}`);\n      for (const line of entry.intro || []) this.say(`\\n${line}`);\n      if (entry.type === "battle") {\n        if (entry.choice === "fight_or_run" && await this.fightOrRun() === "run") {\n          if (entry.run && entry.run.text) this.say(`\\n${entry.run.text}`);\n          if (entry.run && entry.run.game_over) this.gameOver(player);\n          return;\n        }\n        await this.spellFight(entry.enemy, player);\n      }\n      for (const reward of ((entry.victory || {}).rewards || [])) {\n        if (reward.item) player.backpack.push(reward.item);\n        if (reward.money !== undefined) { const v=reward.money; player.money += typeof v === "object" ? randomInt(v.min,v.max) : Number(v); }\n      }\n      if ((entry.victory || {}).offer_potions) await this.offerPotions(player);\n    }\n\n    async runSceneAdditions(sceneId, player) {\n      for (const id of (ENCOUNTER_DATA.scenes[sceneId].after_scene || [])) await this.runJsonEncounter(id, player);\n    }\n\n'''


def patch_python():
    p=STORY; s=p.read_text(encoding='utf-8')
    imp='from .encounter_data import additions, encounter\n'
    if imp not in s: s=s.replace('from .data import LONG_ROAD_ENEMIES\n','from .data import LONG_ROAD_ENEMIES\n'+imp)
    if 'def _run_json_encounter(' not in s: s=s.replace('def _extra_fight(',PYHELP+'\n\ndef _extra_fight(',1)
    marker='    else:\n        raise SaveError("Unknown story checkpoint.")\n'
    if 'for encounter_id in additions(scene_id):' not in s: s=s.replace(marker,marker+'\n    for encounter_id in additions(scene_id):\n        _run_json_encounter(encounter_id, player)\n',1)
    p.write_text(s,encoding='utf-8'); (ROOT/'text_adventure'/'encounter_data.py').write_text(LOADER,encoding='utf-8')


def patch_web():
    p=WEB; s=p.read_text(encoding='utf-8')
    if 'let ENCOUNTER_DATA = null;' not in s:
        s=s.replace('  const FINISHED_SCENE = "finished";\n','  const FINISHED_SCENE = "finished";\n  let ENCOUNTER_DATA = null;\n  async function loadEncounterData() { const r=await fetch("story/encounters.json",{cache:"no-store"}); if(!r.ok) throw new Error(`Encounter data ${r.status}`); ENCOUNTER_DATA=await r.json(); }\n',1)
    if 'async runJsonEncounter(' not in s: s=s.replace('    async extraFight(',JSHELP+'    async extraFight(',1)
    end='      } else {\n        throw new Error("Unknown story checkpoint.");\n      }\n    }\n'
    if 'await this.runSceneAdditions(sceneId, player);' not in s: s=s.replace(end,end[:-6]+'\n      await this.runSceneAdditions(sceneId, player);\n    }\n',1)
    old='    const game = new AdventureGame(terminal);\n    game.start();'
    if 'await loadEncounterData();' not in s: s=s.replace(old,'    await loadEncounterData();\n    const game = new AdventureGame(terminal);\n    await game.start();',1).replace('window.addEventListener("DOMContentLoaded", () => {','window.addEventListener("DOMContentLoaded", async () => {',1)
    p.write_text(s,encoding='utf-8')


def main():
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(build(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    patch_python(); patch_web()
    for name in ('story/realmbound_story.json','tools/story_sync.py','.github/workflows/bootstrap-shared-story.yml'):
        q=ROOT/name
        if q.exists(): q.unlink()
    (ROOT/'story'/'README.md').write_text('# Encounter editor\n\nEdit `story/encounters.json`. It lists every battle, shop, rest stop, and secret without copying source code. To add a battle, put it in `data_encounters` and add its id to a scene\'s `after_scene` list. Python and HTML5 will run it automatically.\n',encoding='utf-8')

if __name__=='__main__': main()
