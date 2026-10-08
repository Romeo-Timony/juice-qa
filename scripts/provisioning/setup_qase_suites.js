const fs = require('fs');
const dotenv = fs.readFileSync('qa-automation/.env', 'utf8');
const env = Object.fromEntries(dotenv.split('\n').filter(l => l.includes('=')).map(l => {
  const idx = l.indexOf('=');
  return [l.slice(0, idx).trim(), l.slice(idx + 1).trim()];
}));

async function main() {
  // 1. Get existing suites
  const res = await fetch(env.QASE_API_URL + '/suite/' + env.QASE_PROJECT_CODE + '?limit=100', {
    headers: { Token: env.QASE_API_TOKEN, Accept: 'application/json' }
  });
  const data = await res.json();
  const suites = data.result?.entities || [];
  console.log('Current suites:', suites.map(s => ({ id: s.id, title: s.title, parent_id: s.parent_id })));

  // Update Suite 1 to exact standard title
  const featTitle = '[JS-15] Модуль аутентификации, авторизации и профиля клиента';
  await fetch(env.QASE_API_URL + '/suite/' + env.QASE_PROJECT_CODE + '/1', {
    method: 'PATCH',
    headers: { Token: env.QASE_API_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: featTitle,
      description: 'Тестовые наборы фичи: регистрация, вход, JWT-сессии, профиль пользователя, аватар и адреса'
    })
  });
  console.log('Updated Suite 1 to:', featTitle);

  // Update Suite 2 to Backend sub-suite
  const beTitle = 'Backend [JS-17]: REST API, JWT и БД';
  await fetch(env.QASE_API_URL + '/suite/' + env.QASE_PROJECT_CODE + '/2', {
    method: 'PATCH',
    headers: { Token: env.QASE_API_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: beTitle,
      parent_id: 1,
      description: 'Серверные проверки REST API эндпоинтов, JWT авторизации, Sequelize ORM и безопасности OWASP'
    })
  });
  console.log('Updated Suite 2 to:', beTitle);

  // Create Frontend sub-suite under Suite 1 if not exists
  let feSuite = suites.find(s => s.title.includes('Frontend') && s.parent_id === 1);
  let feSuiteId;
  if (!feSuite) {
    const feRes = await fetch(env.QASE_API_URL + '/suite/' + env.QASE_PROJECT_CODE, {
      method: 'POST',
      headers: { Token: env.QASE_API_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Frontend [JS-16]: UI, формы и клиентская логика',
        parent_id: 1,
        description: 'Клиентские проверки экранов регистрации, логина, JwtInterceptor, профиля и загрузки аватара'
      })
    });
    const feData = await feRes.json();
    feSuiteId = feData.result.id;
    console.log('Created Frontend Suite:', feSuiteId);
  } else {
    feSuiteId = feSuite.id;
    console.log('Found Frontend Suite:', feSuiteId);
  }

  // Move Cases 57-68 to Frontend Suite
  for (let id = 57; id <= 68; id++) {
    await fetch(env.QASE_API_URL + '/case/' + env.QASE_PROJECT_CODE + '/' + id, {
      method: 'PATCH',
      headers: { Token: env.QASE_API_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ suite_id: feSuiteId })
    });
  }
  console.log('Moved cases 57-68 to Frontend Suite', feSuiteId);

  // Move Cases 69-80 to Backend Suite (id 2)
  for (let id = 69; id <= 80; id++) {
    await fetch(env.QASE_API_URL + '/case/' + env.QASE_PROJECT_CODE + '/' + id, {
      method: 'PATCH',
      headers: { Token: env.QASE_API_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ suite_id: 2 })
    });
  }
  console.log('Moved cases 69-80 to Backend Suite 2');
}
main().catch(console.error);
