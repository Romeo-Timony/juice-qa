// Deploys the QA DoR Gate workflow to n8n and registers the Jira Cloud webhook.
// Required in qa-automation/.env: ATLASSIAN_API_TOKEN, N8N_API_KEY
// Optional: N8N_URL, ATLASSIAN_USER_EMAIL, ATLASSIAN_BASE_URL, GEMINI_MODEL, N8N_JIRA_CRED_ID, N8N_GEMINI_CRED_ID, QASE_API_TOKEN, QASE_PROJECT_CODE
const fs = require('fs')
const path = require('path')
const crypto = require('crypto')
const { buildWorkflow, WEBHOOK_PATH, WORKFLOW_NAME } = require('./build_workflow')

const envCandidates = [path.join(__dirname, '..', '.env'), path.join(__dirname, '..', '..', '.env')]
const envFile = envCandidates.find(f => fs.existsSync(f)) || envCandidates[0]
const env = fs.existsSync(envFile) ? Object.fromEntries(fs.readFileSync(envFile, 'utf8').split(/\r?\n/)
  .filter(l => /^\s*[A-Z0-9_]+=/.test(l))
  .map(l => { const i = l.indexOf('='); return [l.slice(0, i).trim(), l.slice(i + 1).trim()] })) : {}
const cfg = { ...env, ...process.env }

const N8N_URL = (cfg.N8N_URL || cfg.N8N_SERVER_URL || 'http://201.34.147.33:5678').replace(/\/$/, '')
const JIRA_BASE = cfg.ATLASSIAN_BASE_URL || 'https://romeo-timony.atlassian.net'
const JIRA_EMAIL = cfg.ATLASSIAN_USER_EMAIL || 'roman.timoshenko@gmail.com'
const GEMINI_MODEL = cfg.GEMINI_MODEL || 'gemini-3.5-flash'
const STATE_FILE = path.join(__dirname, '.deploy-state.json')
const state = fs.existsSync(STATE_FILE) ? JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')) : {}

if (!cfg.N8N_API_KEY) throw new Error('N8N_API_KEY is missing in .env')
if (!cfg.ATLASSIAN_API_TOKEN) throw new Error('ATLASSIAN_API_TOKEN is missing in .env')

const jiraAuth = 'Basic ' + Buffer.from(`${JIRA_EMAIL}:${cfg.ATLASSIAN_API_TOKEN}`).toString('base64')

async function call (base, method, url, body, headers) {
  const res = await fetch(base + url, {
    method,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...headers },
    body: body ? JSON.stringify(body) : undefined
  })
  const text = await res.text()
  if (!res.ok) throw new Error(`${method} ${url} -> ${res.status}: ${text}`)
  return text ? JSON.parse(text) : {}
}
const n8n = (method, url, body) => call(N8N_URL, method, '/api/v1' + url, body, { 'X-N8N-API-KEY': cfg.N8N_API_KEY })
const jira = (method, url, body) => call(JIRA_BASE, method, url, body, { Authorization: jiraAuth })

async function ensureCredential (key, envId, name, type, data) {
  const id = cfg[envId] || state[key]
  if (id) {
    console.log(`Using existing credential "${name}" (${id})`)
    return { id, name }
  }
  if (!data) throw new Error(`Provide ${envId} or the secret required to create credential "${name}"`)
  const created = await n8n('POST', '/credentials', { name, type, data })
  state[key] = created.id
  console.log(`Created n8n credential "${name}" (${created.id})`)
  return { id: created.id, name }
}

;(async () => {
  console.log('--- Step 1: Resolving Credentials ---')
  const jiraCred = await ensureCredential('jiraCredId', 'N8N_JIRA_CRED_ID', 'Jira Cloud (romeo-timony)', 'jiraSoftwareCloudApi',
    { email: JIRA_EMAIL, apiToken: cfg.ATLASSIAN_API_TOKEN, domain: JIRA_BASE })
  const geminiCred = await ensureCredential('geminiCredId', 'N8N_GEMINI_CRED_ID', 'Google Gemini API', 'googlePalmApi',
    cfg.GEMINI_API_KEY ? { host: 'https://generativelanguage.googleapis.com', apiKey: cfg.GEMINI_API_KEY } : null)
  const qaseCred = await ensureCredential('qaseCredId', 'N8N_QASE_CRED_ID', 'Qase TMS API', 'httpHeaderAuth',
    cfg.QASE_API_TOKEN ? { name: 'Token', value: cfg.QASE_API_TOKEN } : null)

  console.log('\n--- Step 2: Building Workflow ---')
  state.webhookToken = state.webhookToken || crypto.randomBytes(24).toString('hex')
  const wf = buildWorkflow({
    jiraCred,
    geminiCred,
    qaseCred,
    webhookToken: state.webhookToken,
    geminiModel: GEMINI_MODEL,
    qaseCode: cfg.QASE_PROJECT_CODE || 'JS',
    qaseToken: cfg.QASE_API_TOKEN
  })

  console.log('\n--- Step 3: Deploying Workflow to n8n ---')
  let existing = null
  if (state.workflowId) existing = await n8n('GET', `/workflows/${state.workflowId}`).catch(() => null)
  if (!existing) {
    const list = await n8n('GET', '/workflows?limit=250')
    existing = (list.data || []).find(w => w.name === WORKFLOW_NAME) || null
  }

  if (existing) {
    if (existing.active) await n8n('POST', `/workflows/${existing.id}/deactivate`)
    await n8n('PUT', `/workflows/${existing.id}`, wf)
    state.workflowId = existing.id
    console.log(`Updated existing workflow ${existing.id}`)
  } else {
    const created = await n8n('POST', '/workflows', wf)
    state.workflowId = created.id
    console.log(`Created new workflow ${created.id}`)
  }
  await n8n('POST', `/workflows/${state.workflowId}/activate`)
  console.log('Workflow successfully activated!')

  console.log('\n--- Step 4: Configuring Jira Webhook ---')
  const hookName = 'n8n QA DoR Gate (JS -> In Progress)'
  const webhookBase = (cfg.NGROK_URL || N8N_URL).replace(/\/$/, '')
  const hookUrl = `${webhookBase}/webhook/${WEBHOOK_PATH}?token=${state.webhookToken}`
  try {
    const hooks = await jira('GET', '/rest/webhooks/1.0/webhook')
    for (const h of hooks.filter(h => h.name === hookName)) {
      await jira('DELETE', new URL(h.self).pathname)
    }
    const hook = await jira('POST', '/rest/webhooks/1.0/webhook', {
      name: hookName,
      url: hookUrl,
      events: ['jira:issue_updated'],
      filters: { 'issue-related-events-section': 'project = JS' },
      excludeBody: false
    })
    state.jiraWebhook = hook.self
    console.log(`Jira webhook registered: ${hook.self}`)
  } catch (err) {
    console.log(`Note: Jira Cloud requires HTTPS for webhooks (${err.message}).`)
    console.log(`Schedule Trigger is actively polling Jira every 1m for issues in status "В работе".`)
  }

  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2))
  console.log(`\n======================================================`)
  console.log(`Deployment Complete!`)
  console.log(`Workflow URL: ${N8N_URL}/workflow/${state.workflowId}`)
  console.log(`======================================================`)
})().catch(e => { console.error('Deployment Error:', e.message); process.exit(1) })
