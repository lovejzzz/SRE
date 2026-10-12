"""Use the actual installed Python stdlib; read one adapter request on stdin."""
import json
import posixpath
import sys

request = json.load(sys.stdin)
steps = []
for action in request["actions"]:
    steps.append({"action": action, "result": {"value": posixpath.normpath(action["normalize"])},
                  "state": {"stateless": True}})
print(json.dumps({"schema_version": 1, "scenario": request["scenario"],
                  "lifecycle": {"reset": True, "finalize": True}, "steps": steps}, ensure_ascii=True))
