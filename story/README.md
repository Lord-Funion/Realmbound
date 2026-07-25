# Shared Realmbound story source

`realmbound_story.json` is the canonical cross-port story bundle.

Realmbound's ports use different languages, and the C++ and legacy versions
currently live on separate Git branches. A single runtime JSON interpreter
would require replacing every game engine at once. Instead, this repository
uses generated native source:

1. The JSON bundle stores the complete story-bearing source file for every
   port as readable arrays of lines.
2. `tools/story_sync.py apply` regenerates each native source file from the
   bundle.
3. `tools/story_sync.py check` verifies that the generated files still match
   the bundle.

This makes the JSON the source of truth while allowing Python, JavaScript, and
C++ to keep their existing combat, save, terminal, and UI implementations.

## Ports in the bundle

- `python`: `main:text_adventure/story.py`
- `web`: `main:web/app.js`
- `cpp`: `cpp-port:cpp/adventure_game.cpp`
- `legacy`: `legacy:main.py`, when that branch is available

The bundle also exposes the canonical scene order and scene titles separately
at the top, so tools can inspect the story without parsing the source files.

## Refresh the bundle from all ports

Fetch the branches, then extract:

```bash
git fetch origin main cpp-port legacy
python tools/story_sync.py extract
python tools/story_sync.py summary
```

## Edit the story and regenerate a port

Edit `story/realmbound_story.json`, then regenerate the native files on the
appropriate branch or worktree.

On `main`:

```bash
python tools/story_sync.py apply --port python --port web
python tools/story_sync.py check
```

On a C++ worktree:

```bash
git worktree add ../realmbound-cpp cpp-port
python tools/story_sync.py apply \
  --bundle story/realmbound_story.json \
  --root ../realmbound-cpp \
  --port cpp
```

The same pattern works for `legacy`.

## Important rule

Do not edit the generated story files and the JSON separately. Make story
changes in `realmbound_story.json`, apply them to the affected ports, and run
the check before committing.
