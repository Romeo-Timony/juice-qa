"""
Creates and deploys a Global Error Handler Workflow in n8n,
and links it to the main 'Juice Shop' workflow (Dv1WydaTMC1lxR0E).
Whenever any node fails in n8n, an instant crash alert with a direct link
to the failed execution is dispatched to Telegram.
"""

import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding="utf-8")
dotenv.load_dotenv(".env")

N8N_URL = os.getenv("N8N_URL", "http://201.34.147.33:5678").rstrip("/")
N8N_API_KEY = os.getenv("N8N_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8463540623:AAHmW9uuff8C_XQDk4cLby1GoVyc7-zo4Ek")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1434200911")

MAIN_WORKFLOW_ID = "Dv1WydaTMC1lxR0E"

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
}

# 1. Define the Global Error Handler Workflow
error_workflow_payload = {
    "name": "Global QA Error Handler",
    "nodes": [
        {
            "parameters": {},
            "id": "err-trigger-node-01",
            "name": "Error Trigger",
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [200, 300]
        },
        {
            "parameters": {
                "jsCode": """
const err = $json.execution?.error || {};
const wf = $json.workflow || {};
const exec = $json.execution || {};

const wfName = wf.name || 'Unknown Workflow';
const lastNode = err.node?.name || err.lastNodeExecuted || 'Unknown Node';
const errMsg = err.message || 'Unhandled error occurred';
const execId = exec.id || 'N/A';
const execUrl = `${exec.url || 'http://201.34.147.33:5678/execution/' + execId}`;

const text = `🚨 <b>[n8n FLOW FAILURE] Сбой в оркестраторе QA</b>\\n\\n` +
  `📁 <b>Воркфлоу:</b> ${wfName}\\n` +
  `🛑 <b>Упавший узел:</b> <code>${lastNode}</code>\\n` +
  `🆔 <b>Execution ID:</b> <code>#${execId}</code>\\n\\n` +
  `💬 <b>Ошибка:</b>\\n<code>${errMsg.substring(0, 500)}</code>\\n\\n` +
  `🔗 <a href="${execUrl}"><b>👉 Открыть упавший прогон в n8n</b></a>`;

return [{ json: { text, chat_id: '""" + str(CHAT_ID) + """' } }];
"""
            },
            "id": "err-format-code-02",
            "name": "Format Error Card",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [440, 300]
        },
        {
            "parameters": {
                "method": "POST",
                "url": f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ JSON.stringify({ chat_id: $json.chat_id, text: $json.text, parse_mode: 'HTML', disable_web_page_preview: true }) }}"
            },
            "id": "err-tg-send-03",
            "name": "Telegram: Send Error Alert",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [680, 300]
        }
    ],
    "connections": {
        "Error Trigger": {
            "main": [
                [
                    {
                        "node": "Format Error Card",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "Format Error Card": {
            "main": [
                [
                    {
                        "node": "Telegram: Send Error Alert",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    },
    "settings": {
        "executionOrder": "v1"
    }
}


def setup_error_workflow():
    print("=== 1. Проверка существующих воркфлоу n8n ===")
    r = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers)
    r.raise_for_status()
    workflows = r.json().get("data", [])
    
    error_wf_id = None
    for wf in workflows:
        if wf.get("name") == "Global QA Error Handler":
            error_wf_id = wf["id"]
            print(f"Найден существующий Global QA Error Handler ID: {error_wf_id}")
            break

    if error_wf_id:
        print("Обновление существующего Error Handler воркфлоу...")
        up_r = requests.put(f"{N8N_URL}/api/v1/workflows/{error_wf_id}", headers=headers, json=error_workflow_payload)
        up_r.raise_for_status()
    else:
        print("Создание нового Global QA Error Handler воркфлоу...")
        create_r = requests.post(f"{N8N_URL}/api/v1/workflows", headers=headers, json=error_workflow_payload)
        create_r.raise_for_status()
        error_wf_id = create_r.json()["id"]
        print(f"Создан Global QA Error Handler ID: {error_wf_id}")

    # Активируем Error Workflow
    requests.post(f"{N8N_URL}/api/v1/workflows/{error_wf_id}/activate", headers=headers)
    print(f"Воркфлоу {error_wf_id} активирован!")

    # 2. Связываем главный воркфлоу с Error Workflow
    print(f"\n=== 2. Привязка главного воркфлоу ({MAIN_WORKFLOW_ID}) к Error Workflow ({error_wf_id}) ===")
    main_r = requests.get(f"{N8N_URL}/api/v1/workflows/{MAIN_WORKFLOW_ID}", headers=headers)
    main_r.raise_for_status()
    main_data = main_r.json()

    settings = main_data.get("settings", {})
    settings["errorWorkflow"] = error_wf_id
    
    update_main_payload = {
        "name": main_data["name"],
        "nodes": main_data["nodes"],
        "connections": main_data["connections"],
        "settings": settings,
    }
    
    up_main_r = requests.put(f"{N8N_URL}/api/v1/workflows/{MAIN_WORKFLOW_ID}", headers=headers, json=update_main_payload)
    up_main_r.raise_for_status()
    print(f"✅ Главный воркфлоу {MAIN_WORKFLOW_ID} успешно настроен: settings.errorWorkflow = {error_wf_id}")

    # 3. Тестовая отправка через Error Workflow
    print("\n=== 3. Проверка тестовой отправки через Telegram Alert ===")
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    test_msg = (
        "🛡️ <b>[n8n Monitoring Activated]</b>\n"
        "Служба перехвата ошибок <code>Global QA Error Handler</code> успешно подключена к воркфлоу <b>Juice Shop</b>!\n"
        "Любой сбой ноды или таймаут будет мгновенно направляться сюда с прямой ссылкой на execution."
    )
    tg_r = requests.post(tg_url, json={"chat_id": CHAT_ID, "text": test_msg, "parse_mode": "HTML"})
    print("Telegram test delivery status:", tg_r.status_code, tg_r.json().get("ok"))


if __name__ == "__main__":
    setup_error_workflow()
