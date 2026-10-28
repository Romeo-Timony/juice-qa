import json

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == '8672714e-feb5-4242-b9c5-efb63bbbfe20':
        code = n.get('parameters', {}).get('jsCode', '')
        start_idx = code.find('const defaultFrontendCases = [')
        end_idx = code.find('const defaultBackendCases = [')
        if start_idx != -1 and end_idx != -1:
            print("Found block, length:", end_idx - start_idx)
            with open('scripts/tools/frontend_cases_snippet.js', 'w', encoding='utf-8') as sf:
                sf.write(code[start_idx:end_idx])
            print("Snippet saved to scripts/tools/frontend_cases_snippet.js")
