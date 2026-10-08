// n8n Code node: "Сохранение файлов на диск"
const promoted = $('Перенос автотестов в рабочий проект').first().json
const issueKey = promoted.issueKey || 'JS-16'
const files = promoted.promotedFiles || []

// В n8n Code Node мы не можем напрямую использовать require('fs'),
// если переменная окружения NODE_FUNCTION_ALLOW_EXTERNAL не задана.
// Но если этот n8n позволяет fs:
let savedCount = 0;
let errors = [];

try {
  const fs = require('fs');
  const path = require('path');
  
  // Базовая директория qa-automation
  const baseDir = path.resolve(__dirname, '../../../../');
  
  for (const f of files) {
    if (!f.targetPath || !f.finalCode) continue;
    const absPath = path.join(baseDir, f.targetPath);
    
    // Создаем директорию, если нет
    const dir = path.dirname(absPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // Записываем файл
    fs.writeFileSync(absPath, f.finalCode, 'utf8');
    savedCount++;
  }

  // Записываем ID текущего выполнения n8n для GitHub Actions
  const execMetaPath = path.join(baseDir, 'n8n_execution.json');
  fs.writeFileSync(execMetaPath, JSON.stringify({ executionId: $execution.id }), 'utf8');
} catch (e) {
  errors.push(e.message);
}

return [{
  json: {
    issueKey,
    savedCount,
    errors,
    message: savedCount > 0 ? `Успешно сохранено файлов: ${savedCount}` : 'Файлы не сохранены'
  }
}]
