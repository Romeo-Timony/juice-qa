import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_current_workflow.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

print("=== WORKFLOW CONNECTIONS GRAPH ===")
for src, conn in wf.get('connections', {}).items():
    main_outs = conn.get('main', [])
    for out_idx, group in enumerate(main_outs):
        targets = [f"{item['node']} (idx:{item.get('index', 0)})" for item in group]
        if targets:
            print(f"[{src}] (output {out_idx}) --> {', '.join(targets)}")
