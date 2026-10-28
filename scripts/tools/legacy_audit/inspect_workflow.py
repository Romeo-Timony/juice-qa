import json

d = json.load(open('n8n/current_main_workflow.json', encoding='utf-8'))
nodes = d.get('nodes', [])

sticky = [n for n in nodes if n.get('type') == 'n8n-nodes-base.stickyNote']
other = [n for n in nodes if n.get('type') != 'n8n-nodes-base.stickyNote']

with open('n8n/workflow_structure.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total nodes: {len(nodes)}, Sticky: {len(sticky)}, Functional: {len(other)}\n")
    out.write("\n--- STICKY NOTES ---\n")
    for s in sticky:
        content = s.get('parameters', {}).get('content', '')
        pos = s.get('position', [])
        w = s.get('parameters', {}).get('width', 0)
        h = s.get('parameters', {}).get('height', 0)
        out.write(f"Sticky '{s.get('name')}' at {pos} [w={w}, h={h}]:\n{content}\n" + "-"*40 + "\n")

    out.write("\n--- FUNCTIONAL NODES ---\n")
    for o in other:
        name = o.get('name')
        ntype = o.get('type')
        pos = o.get('position', [])
        out.write(f"[{pos[0]}, {pos[1]}] {name} ({ntype})\n")

