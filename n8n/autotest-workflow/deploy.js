const fs = require('fs')
const path = require('path')
const axios = require('axios')
require('dotenv').config({ path: path.join(__dirname, '../../.env') })

const N8N_URL = process.env.N8N_SERVER_URL || 'http://localhost:5678'
const N8N_API_KEY = process.env.N8N_API_KEY

if (!N8N_API_KEY) {
  console.error('Missing N8N_API_KEY in .env')
  process.exit(1)
}

async function deploy() {
  const workflowData = JSON.parse(fs.readFileSync(path.join(__dirname, 'autotest_workflow.json')))
  
  const stateFile = path.join(__dirname, '.deploy-state.json')
  let workflowId = null
  if (fs.existsSync(stateFile)) {
    workflowId = JSON.parse(fs.readFileSync(stateFile)).workflowId
  }

  const client = axios.create({
    baseURL: N8N_URL + '/api/v1',
    headers: { 'X-N8N-API-KEY': N8N_API_KEY }
  })

  try {
    if (workflowId) {
      await client.put(`/workflows/${workflowId}`, workflowData)
      console.log(`Workflow updated: ${workflowId}`)
    } else {
      const res = await client.post('/workflows', workflowData)
      workflowId = res.data.id
      fs.writeFileSync(stateFile, JSON.stringify({ workflowId }))
      console.log(`Workflow created: ${workflowId}`)
    }
    
    await client.post(`/workflows/${workflowId}/activate`, {})
    console.log('Workflow activated!')
  } catch (e) {
    console.error('Error deploying workflow:', e.response?.data || e.message)
  }
}

deploy()
