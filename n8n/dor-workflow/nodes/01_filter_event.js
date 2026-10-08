// n8n Code node: "Filter: moved to In Progress"
const CONFIG = {
  jiraBase: 'https://romeo-timony.atlassian.net',
  projectKey: 'JS',
  inProgressStatusId: '10046',
  inProgressNames: ['В работе', 'In Progress'],
  todoStatusId: '10045',
  geminiModel: '__GEMINI_MODEL__',
  webhookToken: '__WEBHOOK_TOKEN__'
}

const out = []
for (const item of $input.all()) {
  const json = item.json || {}

  // Case A: From Polling (Jira Search API)
  if (json.issues && Array.isArray(json.issues)) {
    for (const issue of json.issues) {
      out.push({
        json: {
          issueKey: issue.key,
          issueId: issue.id,
          fromStatus: 'К выполнению',
          toStatus: 'В работе',
          actor: (issue.fields && issue.fields.assignee) ? issue.fields.assignee.displayName : 'system',
          receivedAt: new Date().toISOString(),
          config: CONFIG
        }
      })
    }
    continue
  }

  // Case C: From MCP Trigger (Direct execution)
  if (json.issueKey && typeof json.issueKey === 'string') {
    out.push({
      json: {
        issueKey: json.issueKey,
        issueId: json.issueId || 'unknown',
        fromStatus: 'К выполнению',
        toStatus: 'В работе',
        actor: json.actor || 'mcp-agent',
        receivedAt: new Date().toISOString(),
        config: CONFIG
      }
    })
    continue
  }

  // Case D: Fallback for manual click "Execute Workflow" (Empty input)
  if (Object.keys(json).length === 0) {
    out.push({
      json: {
        issueKey: 'JS-16',
        issueId: '10016',
        fromStatus: 'К выполнению',
        toStatus: 'В работе',
        actor: 'manual-tester',
        receivedAt: new Date().toISOString(),
        config: CONFIG
      }
    })
    continue
  }

  // Case B: From Webhook
  const req = json
  if (CONFIG.webhookToken && (req.query || {}).token !== CONFIG.webhookToken) continue

  const body = req.body || {}
  const issue = body.issue
  if (!issue || body.webhookEvent !== 'jira:issue_updated') continue
  if (!String(issue.key).startsWith(CONFIG.projectKey + '-')) continue

  const change = ((body.changelog || {}).items || []).find(i =>
    i.field === 'status' &&
    (String(i.to) === CONFIG.inProgressStatusId || CONFIG.inProgressNames.includes(i.toString))
  )
  if (!change) continue

  out.push({
    json: {
      issueKey: issue.key,
      issueId: issue.id,
      fromStatus: change.fromString,
      toStatus: change.toString,
      actor: (body.user || {}).displayName || 'unknown',
      receivedAt: new Date().toISOString(),
      config: CONFIG
    }
  })
}

return out
