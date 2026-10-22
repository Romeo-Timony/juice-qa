import re
from pathlib import Path

path = Path('qa-automation/tests/ui/auth/test_auth_ui.py')
content = path.read_text(encoding='utf-8')

replacements = [
    ('532', '561'),
    ('533', '562'),
    ('534', '563'),
    ('535', '564'),
    ('536', '565'),
    ('537', '566'),
    ('539', '568'),
    ('540', '569'),
    ('541', '570'),
]

for old_id, new_id in replacements:
    content = content.replace(f"TC-{old_id}", f"TC-{new_id}")
    content = content.replace(f"case/{old_id}", f"case/{new_id}")
    content = content.replace(f"id={old_id}", f"id={new_id}")
    content = content.replace(f"tc{old_id}", f"tc{new_id}")

path.write_text(content, encoding='utf-8')
print("Successfully updated test_auth_ui.py with Qase IDs 561..570")
