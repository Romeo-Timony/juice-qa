import json

d = json.load(open("n8n/current_main_workflow.json", encoding="utf-8"))
for n in d["nodes"]:
    if n.get("type") == "n8n-nodes-base.stickyNote":
        p = n.get("parameters", {})
        print(f"Name: {n.get('name')}")
        print(f"  Pos: {n.get('position')}, w={p.get('width')}, h={p.get('height')}, color={p.get('color')}")
