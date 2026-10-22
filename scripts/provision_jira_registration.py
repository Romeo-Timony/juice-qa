#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Официальный скрипт провижининга пользовательской истории и инженерных задач
по модулю регистрации (User Registration) на базе живой документации Confluence.
Использует универсальный движок `confluence_to_jira.py` с гарантией 100% DoR Gate.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from confluence_to_jira import sync_spec_from_confluence

if __name__ == "__main__":
    # Page ID 3604481: JS-100 Регистрация нового пользователя
    page_id = os.getenv("CONFLUENCE_REGISTRATION_PAGE_ID", "3604481")
    
    # Если передан флаг --new, создаст новую ветку задач. По умолчанию обновляет текущие эталонные JS-39..42.
    if "--new" in sys.argv:
        sync_spec_from_confluence(page_id=page_id, existing_keys=None, dry_run=False)
    else:
        existing = {
            'story': 'JS-39',
            'api': 'JS-40',
            'ui': 'JS-41',
            'e2e': 'JS-42'
        }
        sync_spec_from_confluence(page_id=page_id, existing_keys=existing, dry_run=False)
