import json

with open('qa-automation/jira_js16_spec.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

def extract_text(node):
    if isinstance(node, dict):
        node_type = node.get('type')
        if node_type == 'text':
            return node.get('text', '')
        if node_type == 'inlineCard':
            return node.get('attrs', {}).get('url', '')
        t = ''
        for child in node.get('content', []):
            t += extract_text(child)
        if node_type in ['paragraph', 'heading']:
            return t + '\n\n'
        if node_type in ['listItem']:
            return '- ' + t + '\n'
        if node_type in ['tableRow']:
            return '| ' + t.replace('\n', ' | ') + ' |\n'
        if node_type in ['tableCell', 'tableHeader']:
            return t.strip() + ' | '
        return t
    elif isinstance(node, list):
        return ''.join(extract_text(x) for x in node)
    return ''

txt = extract_text(d['description'])
with open('qa-automation/jira_js16_spec_parsed.md', 'w', encoding='utf-8') as f:
    f.write(f"# {d['summary']}\n\n" + txt)
print('Successfully parsed to qa-automation/jira_js16_spec_parsed.md')
