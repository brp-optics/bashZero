# bashZero
Track progress toward inboxZero-style goals from the command line. Currently supports number of files in a local folder.

AGPLv3-licensed; 100% hand-coded; only external dependency is matplotlib

requires python > 3.4

Current install:
```bash
git clone https://github.com/brp-optics/bashZero
cd bashZero
uv sync
```

Current usage: 

```bash
uv run python3 src/bashZero.py
```

Goal (not yet implemented):
```bash
python3 bashZero add-folder goal 10 rate -10 
```
