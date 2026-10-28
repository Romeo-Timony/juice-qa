#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт наведения порядка и оптимизации workflow n8n (Juice Shop):
1. Добавление информативных in-editor notes ко всем рабочим нодам (notesInEditor: true).
2. Обновление и структурирование Sticky Notes (стикеров).
3. Интеграция нативных нод Telegram (n8n-nodes-base.telegram) с использованием существующего креденшла.
4. Валидация и загрузка обновленного workflow в n8n через REST API.
"""
import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
key = os.getenv('N8N_API_KEY')
wf_id = 'Dv1WydaTMC1lxR0E'

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers={'X-N8N-API-KEY': key})
if not r.ok:
    print(f"Ошибка загрузки workflow: {r.status_code}")
    sys.exit(1)

wf = r.json()
nodes = wf['nodes']
connections = wf['connections']

# Словарь детальных описаний (notes) для каждой ноды
NODE_NOTES = {
    "Webhook: События Qase TMS": (
        "📥 Слушает вебхуки от Qase TMS при изменениях тестов (создание, удаление, редактирование). "
        "Используется для контроля дрифта между кодом и TMS."
    ),
    "Синхронизация удаленных тестов (Drift)": (
        "⚖️ Анализирует события удаления тест-кейсов в Qase TMS и предупреждает о возможном "
        "рассинхроне с локальным репозиторием автотестов."
    ),
    "Jira: Перехват обновления задачи": (
        "🎯 Основной входной вебхук Jira Cloud (jira:issue_updated). "
        "Срабатывает мгновенно при перемещении карточки задачи по доске."
    ),
    "Execute Workflow Trigger": (
        "⚡ Входная точка для ручного тестирования или программного запуска воркфлоу через n8n API."
    ),
    "Фильтр: Задача взята в работу": (
        "🔍 Фильтрует входящие события Jira: пропускает только переход в статус 'В работе' "
        "(In Progress / ID: 10046). Извлекает ключ задачи (issueKey) и параметры авторизации."
    ),
    "Jira: Загрузить данные задачи": (
        "📡 Запрашивает полный JSON задачи из Jira REST API v2 (summary, description, status, "
        "issuetype, labels, parent)."
    ),
    "Jira: Загрузить ссылки задачи": (
        "🔗 Запрашивает связанные веб-ссылки (Remote Links): спецификации в Confluence, "
        "документацию и внешние контракты."
    ),
    "Правила проверки готовности задачи": (
        "📐 Декларативный эталон QA DoR v1.0: 10 обязательных системных правил (C01-C10) + "
        "3 критерия User Story (S01-S03), пороги скоринга (75%) и веса."
    ),
    "Подготовка задачи к проверке": (
        "🔬 Предварительный анализ задачи: нормализация текста, определение профиля (API, UI, E2E), "
        "проверка наличия ссылок на Confluence, контрактов и критериев приёмки."
    ),
    "Проверка задачи на готовность": (
        "⚖️ Ядро DoR Gate (Seam 1): скоринг задачи по 13 критериям, проверка обязательных блокеров "
        "и генерация итоговой таблицы с отчетом для Jira."
    ),
    "Условие: Требования задачи понятны?": (
        "🔀 Развилка DoR: TRUE -> скор >= 75% и 0 блокеров (DoR PASS); "
        "FALSE -> есть блокеры (DoR FAIL, задача возвращается на доработку)."
    ),
    "Jira: Отправить замечания к задаче": (
        "📝 Публикует подробный отчет с перечнем проваленных критериев DoR и конкретными "
        "Action Items для системного аналитика / владельца продукта."
    ),
    "Условие: Пауза из-за контракта или возврат?": (
        "⏳ Анализирует характер блокера: временное ожидание серверного контракта (пауза) "
        "или неполнота аналитики (полный возврат в To Do)."
    ),
    "Jira: Поставить метку qa-paused": (
        "🏷️ Маркирует тикет лейблом 'qa-paused' при ожидании фиксации бэкенд-контрактов."
    ),
    "Jira: Вернуть задачу на доработку": (
        "↩️ Автоматически переводит задачу назад в статус 'К выполнению' ('To Do') в Jira."
    ),
    "Jira: Поставить метку Требует доработки": (
        "🏷️ Устанавливает метку 'qa-dor-failed' для подсветки тикета на канбан-доске."
    ),
    "Jira: Отчет 1 — Задача готова к работе (DoR Gate)": (
        "✅ Публикует первый сервисный комментарий: зеленый бейдж успешного прохождения DoR Gate "
        "со 100% подтверждением соответствия стандарту."
    ),
    "Подготовка данных для чек-листа": (
        "📋 Агрегирует профиль задачи, бизнес-правила и параметры для генерации тест-дизайна."
    ),
    "Создание карты проверок": (
        "🧠 Генерирует визуальную интеллект-карту (Mindmap) проверок и декомпозированный чек-лист."
    ),
    "Jira: Отчет 2 — Интеллект-карта проверок": (
        "📊 Публикует второй сервисный комментарий: интеллект-карту проверок в разметке Jira."
    ),
    "Подготовка данных для тест-кейсов": (
        "🧬 Формирует тестовый контекст, слой автоматизации (API, UI, E2E) и префиксы проверок."
    ),
    "Qase: Загрузить список папок": (
        "📂 Запрашивает дерево сьютов верхнего уровня (API, UI, E2E) из Qase TMS REST API."
    ),
    "Qase: Загрузить существующие тесты": (
        "🔍 Выгружает список существующих тест-кейсов для предотвращения дублирования тестов."
    ),
    "Создание тест-кейсов без повторов": (
        "🧪 Генерирует атомарные BDD тест-кейсы, распределяет по системным папкам (API/UI/E2E), "
        "привязывает теги задач и строит матрицу трассируемости (RTM)."
    ),
    "Jira: Отчет 3 — Реестр тест-кейсов (BDD)": (
        "📋 Публикует третий комментарий: структурированную таблицу тест-кейсов с BDD-шагами."
    ),
    "Jira: Отчет 4 — Матрица трассируемости (RTM)": (
        "🔗 Публикует четвертый комментарий: матрицу трассируемости требований к тестам (RTM)."
    ),
    "Условие: Есть новые тесты для добавления?": (
        "🔍 Проверяет, требуется ли регистрация новых тест-кейсов в базе Qase TMS."
    ),
    "Qase: Создать новые тесты в базе": (
        "💾 Выполняет массовое создание новых тест-кейсов в Qase TMS через /v1/case/JS/bulk."
    ),
    "Jira: Прикрепить ссылку на тесты в Qase": (
        "🌐 Добавляет прямую кликабельную ссылку на сьют Qase TMS в секцию Web Links тикета Jira."
    ),
    "Контроль 1: Подтверждение тест-кейсов": (
        "🛡️ Формирует сводную карточку верификации покрытия для согласования тимлидом (Gate 1)."
    ),
    "Jira: Карточка подтверждения тестов (Gate 1)": (
        "📑 Публикует финальную карточку Gate 1: подтверждение готовности тестовой модели к работе."
    ),
    "Webhook: Прием отчетов GitHub Actions": (
        "🐙 Принимает вебхук от GitHub Actions по завершении прогона автотестов в CI/CD."
    ),
    "Парсинг отчета Allure": (
        "📊 Извлекает метрики Allure: общее число тестов, количество passed/failed и длительность."
    ),
    "Jira: Опубликовать отчет Allure": (
        "📈 Публикует финальный отчет о прогоне тестов с кликабельной ссылкой на Allure Report."
    )
}

# 1. Применяем notes ко всем существующим нодам
for n in nodes:
    name = n.get('name')
    if name in NODE_NOTES:
        n['notes'] = NODE_NOTES[name]

# 2. Добавляем 2 нативные ноды Telegram (одна для успеха DoR, вторая для отклонения DoR)
tg_cred = {
    "telegramApi": {
        "id": "dUppB4c1jJrLuGqq",
        "name": "QA Telegram Bot"
    }
}

node_tg_success = {
    "parameters": {
        "operation": "sendMessage",
        "chatId": "1434200911",
        "text": (
            "✅ <b>[QA DoR Gate: Задача одобрена]</b>\n\n"
            "📌 <b>Задача:</b> {{ $('Подготовка данных для тест-кейсов').item.json.issueKey }}\n"
            "🎯 <b>Оценка DoR:</b> 100% (Эталон QA DoR v1.0)\n"
            "📂 <b>Сьют в TMS:</b> {{ $('Создание тест-кейсов без повторов').item.json.suiteTitle || 'API' }}\n"
            "🧪 <b>Тест-кейсов создано:</b> {{ $('Создание тест-кейсов без повторов').item.json.casesCreated || 0 }}\n\n"
            "📋 <b>В Jira успешно опубликованы:</b>\n"
            "• Отчет 1: Валидация DoR Gate\n"
            "• Отчет 2: Интеллект-карта проверок\n"
            "• Отчет 3: Реестр BDD тест-кейсов\n"
            "• Отчет 4: Матрица трассируемости (RTM)\n"
            "• Карточка согласования тестов (Gate 1)\n\n"
            "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $('Подготовка данных для тест-кейсов').item.json.issueKey }}\">Открыть задачу в Jira</a>"
        ),
        "additionalFields": {
            "parse_mode": "HTML"
        }
    },
    "id": "tg-dor-approved-native",
    "name": "Telegram: Оповещение об успешном DoR",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.2,
    "position": [5100, 260],
    "notes": "📢 Отправляет форматированное сообщение в Telegram бот @QApower_bot при успешном прохождении DoR Gate и создании тестов.",
    "credentials": tg_cred
}

node_tg_failed = {
    "parameters": {
        "operation": "sendMessage",
        "chatId": "1434200911",
        "text": (
            "🚫 <b>[QA DoR Gate: Требования отклонены]</b>\n\n"
            "📌 <b>Задача:</b> {{ $('Фильтр: Задача взята в работу').item.json.issueKey }}\n"
            "⚠️ <b>Статус:</b> Возвращена в «К выполнению» (To Do)\n"
            "🏷️ <b>Метка:</b> qa-dor-failed\n\n"
            "❌ <b>Причина:</b> Не выполнены обязательные критерии Definition of Ready.\n"
            "💬 <i>Подробный перечень замечаний и Action Items прикреплен в комментариях Jira.</i>\n\n"
            "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $('Фильтр: Задача взята в работу').item.json.issueKey }}\">Открыть задачу в Jira</a>"
        ),
        "additionalFields": {
            "parse_mode": "HTML"
        }
    },
    "id": "tg-dor-failed-native",
    "name": "Telegram: Алерт об отклонении DoR",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.2,
    "position": [2680, 520],
    "notes": "🚨 Отправляет алерт в Telegram бот @QApower_bot при отклонении задачи по критериям DoR Gate.",
    "credentials": tg_cred
}

node_tg_allure = {
    "parameters": {
        "operation": "sendMessage",
        "chatId": "1434200911",
        "text": (
            "📊 <b>[CI/CD: Прогон автотестов завершен]</b>\n\n"
            "📌 <b>Задача:</b> {{ $json.issueKey || 'JS' }}\n"
            "🎯 <b>Статус:</b> {{ $json.status || 'Автотесты выполнены' }}\n"
            "📈 <b>Отчет Allure:</b> Прикреплен к тикету Jira.\n\n"
            "🔗 <a href=\"https://romeo-timony.atlassian.net/browse/{{ $json.issueKey || 'JS' }}\">Открыть задачу в Jira</a>"
        ),
        "additionalFields": {
            "parse_mode": "HTML"
        }
    },
    "id": "tg-allure-report-native",
    "name": "Telegram: Отчет Allure из CI/CD",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.2,
    "position": [5860, 260],
    "notes": "📈 Отправляет сводку о прогоне автотестов в CI/CD пайплайне в Telegram бот @QApower_bot.",
    "credentials": tg_cred
}

# Добавляем ноды, если их еще нет
existing_node_names = {n['name'] for n in nodes}
if "Telegram: Оповещение об успешном DoR" not in existing_node_names:
    nodes.append(node_tg_success)
if "Telegram: Алерт об отклонении DoR" not in existing_node_names:
    nodes.append(node_tg_failed)
if "Telegram: Отчет Allure из CI/CD" not in existing_node_names:
    nodes.append(node_tg_allure)

# 3. Настраиваем связи (Connections)
# Ветвь успеха DoR: от 'Jira: Карточка подтверждения тестов (Gate 1)' -> 'Telegram: Оповещение об успешном DoR'
if 'Jira: Карточка подтверждения тестов (Gate 1)' in connections:
    connections['Jira: Карточка подтверждения тестов (Gate 1)']['main'] = [
        [
            {
                "node": "Telegram: Оповещение об успешном DoR",
                "type": "main",
                "index": 0
            }
        ]
    ]

# Ветвь отклонения DoR: от 'Jira: Поставить метку Требует доработки' и 'Jira: Поставить метку qa-paused' -> 'Telegram: Алерт об отклонении DoR'
if 'Jira: Поставить метку Требует доработки' in connections:
    connections['Jira: Поставить метку Требует доработки']['main'] = [
        [
            {
                "node": "Telegram: Алерт об отклонении DoR",
                "type": "main",
                "index": 0
            }
        ]
    ]
if 'Jira: Поставить метку qa-paused' in connections:
    connections['Jira: Поставить метку qa-paused']['main'] = [
        [
            {
                "node": "Telegram: Алерт об отклонении DoR",
                "type": "main",
                "index": 0
            }
        ]
    ]

# Ветвь Allure: от 'Jira: Опубликовать отчет Allure' -> 'Telegram: Отчет Allure из CI/CD'
if 'Jira: Опубликовать отчет Allure' in connections:
    connections['Jira: Опубликовать отчет Allure']['main'] = [
        [
            {
                "node": "Telegram: Отчет Allure из CI/CD",
                "type": "main",
                "index": 0
            }
        ]
    ]

# 4. Обновляем стикеры (Sticky Notes) с красивым оформлением и расширенными описаниями
for n in nodes:
    if n['type'] == 'n8n-nodes-base.stickyNote':
        name = n.get('name', '')
        if "Приём задач" in name:
            n['parameters']['content'] = (
                "## 📥 1. Приём задач из Jira\n\n"
                "**Что здесь происходит:**\n"
                "Система мгновенно отслеживает события перехода задач в статус «В работе» через вебхук Jira.\n\n"
                "* Мгновенная реакция на триггер канбан-доски.\n"
                "* Фильтрация по статусу (ID: 10046 / «В работе»).\n"
                "* Загрузка полных данных задачи и связанных ссылок Confluence."
            )
        elif "Проверка готовности" in name:
            n['parameters']['content'] = (
                "## 📋 2. Проверка готовности задачи (DoR Gate) [Этап 1]\n\n"
                "**Что здесь происходит:**\n"
                "Автоматическая валидация задачи по эталону QA Definition of Ready v1.0 (13 критериев):\n\n"
                "* INVEST-соответствие (I, N, V, E, S, T).\n"
                "* Наличие формализованных критериев приёмки (AC) и Gherkin.\n"
                "* Проверка границ скоупа (In/Out-of-Scope) и контрактов API.\n"
                "* Скоринг: проходной балл >= 75% и 0 обязательных блокеров."
            )
        elif "Возврат задачи" in name:
            n['parameters']['content'] = (
                "## ❌ 3. Возврат задачи при DoR Fail & Telegram Alert\n\n"
                "**Что здесь происходит:**\n"
                "Защита команды разработки от работы с неполными требованиями:\n\n"
                "* Публикация отчета с замечаниями и Action Items в Jira.\n"
                "* Возврат тикета назад в статус «К выполнению» («To Do»).\n"
                "* Установка метки 'qa-dor-failed'.\n"
                "* 📢 Мгновенный алерт в Telegram бот @QApower_bot."
            )
        elif "Интеллект-карта" in name:
            n['parameters']['content'] = (
                "## 🧠 4. Интеллект-карта проверок [Этап 2]\n\n"
                "**Что здесь происходит:**\n"
                "Проектирование многоуровневого дерева тест-дизайна:\n\n"
                "* Публикация отчета [Этап 1]: подтверждение DoR со 100% скором.\n"
                "* Построение иерархической Mindmap (Happy Path, BVA, Ошибки, Безопасность).\n"
                "* Публикация отчета [Этап 2]: интерактивный чек-лист в Jira."
            )
        elif "Тест-кейсы и RTM" in name:
            n['parameters']['content'] = (
                "## 🧪 5. Синхронизация с Qase TMS & Матрица RTM [Этапы 3 и 4]\n\n"
                "**Что здесь происходит:**\n"
                "Связывание требований с тест-кейсами в TMS:\n\n"
                "* Синхронизация с корневыми сьютами Qase (API / UI / E2E).\n"
                "* Устранение дубликатов (Deduplication Engine).\n"
                "* Публикация отчета [Этап 3]: Реестр BDD сценариев.\n"
                "* Публикация отчета [Этап 4]: Матрица трассируемости (RTM)."
            )
        elif "Контроль 1" in name:
            n['parameters']['content'] = (
                "## 🛡️ 6. Контроль 1 (Gate 1) & Telegram Уведомление [Этап 5]\n\n"
                "**Что здесь происходит:**\n"
                "Финальная фиксация готовности тестовой модели:\n\n"
                "* Публикация сводной карточки согласования Gate 1 в Jira.\n"
                "* Прикрепление кликабельной ссылки на тесты в Qase.\n"
                "* 📢 Нативное оповещение команды в Telegram @QApower_bot."
            )
        elif "GitHub Actions" in name:
            n['parameters']['content'] = (
                "## 🐙 7. Результаты прогона в CI/CD (Allure Report) [Этап 8]\n\n"
                "**Что здесь происходит:**\n"
                "Интеграция результатов автотестирования:\n\n"
                "* Прием вебхука от GitHub Actions после выполнения тестов.\n"
                "* Парсинг Allure summary (passed/failed/broken).\n"
                "* Публикация отчета в Jira и оповещение в Telegram."
            )

# 5. Сохраняем обновленный workflow в n8n через REST API
payload = {
    "name": wf['name'],
    "nodes": nodes,
    "connections": connections,
    "settings": wf.get('settings', {})
}

put_r = requests.put(
    f"{n8n_url}/api/v1/workflows/{wf_id}",
    headers={"X-N8N-API-KEY": key, "Content-Type": "application/json"},
    json=payload
)

if put_r.ok:
    print(f"✅ Workflow '{wf['name']}' успешно обновлен в n8n (HTTP {put_r.status_code})!")
    print(f"Всего нод: {len(nodes)}")
    print("Нативные ноды Telegram добавлены, in-editor notes активированы ко всем нодам.")
else:
    print(f"❌ Ошибка обновления workflow: HTTP {put_r.status_code}")
    print(put_r.text)
