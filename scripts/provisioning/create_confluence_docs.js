const https = require('https');

const email = 'roman.timoshenko@gmail.com';
const token = 'ATATT3xFfGF0fsfN5tTbmDMnKCM6GKKC3jeEDRBn31rScNDSMDI7LJhw7iihh_TMPq0ZhYcqd0t9CXMbS4zxcTzv44hzpt83RJw9Q6gzJ5VxGLnSVkqE4EaJ32dogjqQnkXX7iq6uCGc_KOlUGKeAnKjClPzKGMrGJSECkCK56TPvvXUfD4k4lI=2DFEDCC0';
const auth = Buffer.from(email + ':' + token).toString('base64');
const spaceKey = 'JS';
const homePageId = '65927';

function apiRequest(path, method, data) {
  return new Promise((resolve, reject) => {
    const postData = data ? JSON.stringify(data) : null;
    const headers = {
      'Authorization': 'Basic ' + auth,
      'Accept': 'application/json'
    };
    if (postData) {
      headers['Content-Type'] = 'application/json';
    }

    const req = https.request({
      hostname: 'romeo-timony.atlassian.net',
      path,
      method,
      headers
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(d));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${d}`));
        }
      });
    });

    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function createPage(title, htmlContent, parentId) {
  const payload = {
    type: 'page',
    title,
    space: { key: spaceKey },
    body: {
      storage: {
        value: htmlContent,
        representation: 'storage'
      }
    }
  };
  if (parentId) {
    payload.ancestors = [{ id: String(parentId) }];
  }
  return await apiRequest('/wiki/rest/api/content', 'POST', payload);
}

// Epic HTML
const epicContent = `
<p><strong>Добро пожаловать в системную спецификацию проекта OWASP Juice Shop!</strong></p>

<h2>1. Паспорт Эпика</h2>
<table>
  <thead>
    <tr>
      <th>Параметр</th>
      <th>Значение</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Ключ Jira</strong></td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong> (Разработка ключевых функциональных модулей веб-приложения OWASP Juice Shop)</a></td>
    </tr>
    <tr>
      <td><strong>Пространство Confluence</strong></td>
      <td><strong>OWASP Juice Shop (JS)</strong></td>
    </tr>
    <tr>
      <td><strong>Статус эпика</strong></td>
      <td><span style="color: green; font-weight: bold;">IN PROGRESS</span></td>
    </tr>
    <tr>
      <td><strong>Ведущий системный аналитик</strong></td>
      <td>Roman Timoshenko</td>
    </tr>
    <tr>
      <td><strong>Стек технологий</strong></td>
      <td>Frontend: Angular 21, TypeScript, Material Design | Backend: Node.js, Express, Sequelize ORM | DB: SQLite / MarsDB</td>
    </tr>
  </tbody>
</table>

<h2>2. Бизнес-цели и концепция проекта</h2>
<p>Веб-приложение <strong>OWASP Juice Shop</strong> представляет собой полнофункциональную платформу электронной коммерции, моделирующую интернет-магазин органических соков и мерчандайза. Данный эпик регламентирует системное проектирование и реализацию всех базовых функциональных модулей интернет-магазина, обеспечивающих полный жизненный цикл покупки: от поиска и формирования корзины до оплаты, пост-обслуживания и интерактивной панели заданий.</p>

<h2>3. Матрица трассируемости модулей (Traceability Matrix)</h2>
<table>
  <thead>
    <tr>
      <th>ID задачи</th>
      <th>Функциональный модуль</th>
      <th>Тип задачи</th>
      <th>Ссылка на задачу в Jira</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>JS-3</strong></td>
      <td>Модуль аутентификации, авторизации и управления профилем клиента</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-3">Перейти к JS-3</a></td>
    </tr>
    <tr>
      <td><strong>JS-4</strong></td>
      <td>Модуль каталога товаров, карточек продуктов и поисковой фильтрации</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-4">Перейти к JS-4</a></td>
    </tr>
    <tr>
      <td><strong>JS-5</strong></td>
      <td>Модуль корзины покупателя (Shopping Basket) и промо-акций</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-5">Перейти к JS-5</a></td>
    </tr>
    <tr>
      <td><strong>JS-6</strong></td>
      <td>Модуль оформления заказа, выбора доставки и проведения платежа (Checkout Flow)</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-6">Перейти к JS-6</a></td>
    </tr>
    <tr>
      <td><strong>JS-7</strong></td>
      <td>Модуль отзывов о товарах и формы обратной связи (Feedback &amp; Reviews)</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-7">Перейти к JS-7</a></td>
    </tr>
    <tr>
      <td><strong>JS-8</strong></td>
      <td>Модуль виртуального ассистента поддержки клиентов (Chatbot "Juicy")</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-8">Перейти к JS-8</a></td>
    </tr>
    <tr>
      <td><strong>JS-9</strong></td>
      <td>Модуль администрирования пользователей и мониторинга заказов (Admin Panel)</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-9">Перейти к JS-9</a></td>
    </tr>
    <tr>
      <td><strong>JS-10</strong></td>
      <td>Модуль интерактивной доски заданий и геймификации (Score Board &amp; Challenges)</td>
      <td>User Story</td>
      <td><a href="https://romeo-timony.atlassian.net/browse/JS-10">Перейти к JS-10</a></td>
    </tr>
  </tbody>
</table>

<h2>4. Общие критерии готовности (Definition of Done - DoD)</h2>
<ul>
  <li>Все функциональные требования (FR) реализованы и согласованы со спецификацией в Confluence.</li>
  <li>Разработаны unit-тесты (Vitest/Jest) и компонентные тесты с покрытием кода не менее 80%.</li>
  <li>Сквозные E2E сценарии автоматизированы на Playwright (соответствие BDD-сценариям).</li>
  <li>Пройден аудит безопасности и соблюдены требования NFR.</li>
  <li>Код прошел Code Review и успешно скомпилирован в CI/CD пайплайне.</li>
</ul>
`;

const modulePages = [
  {
    title: 'JS-3: Модуль аутентификации, авторизации и управления профилем клиента',
    jiraKey: 'JS-3',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-3"><strong>JS-3</strong>: Модуль аутентификации, авторизации и управления профилем клиента</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>High / Critical</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как зарегистрированный или новый клиент веб-магазина Juice Shop,<br/>
Я хочу иметь возможность безопасно регистрироваться, входить в систему, управлять персональными данными (адреса, платежные реквизиты) и восстанавливать пароль,<br/>
Чтобы совершать покупки от своего имени, отслеживать историю заказов и сохранять персональные настройки безопасности.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-AUTH-01:</strong> Email пользователя должен быть уникальным в системе (case-insensitive).</li>
  <li><strong>BR-AUTH-02:</strong> Пароль должен содержать минимум 5 символов. Поддерживается отображение индикатора стойкости пароля.</li>
  <li><strong>BR-AUTH-03:</strong> Для сброса пароля пользователь обязан предоставить ответ на заранее выбранный контрольный вопрос.</li>
  <li><strong>BR-AUTH-04:</strong> При успешном входе клиенту выдается JWT-токен со сроком действия, используемый для авторизации API-запросов.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>RegisterComponent</code> (<code>/#/register</code>) — форма регистрации нового пользователя.</li>
  <li><code>LoginComponent</code> (<code>/#/login</code>) — форма аутентификации.</li>
  <li><code>ForgotPasswordComponent</code> (<code>/#/forgot-password</code>) — форма сброса пароля.</li>
  <li><code>UserProfileComponent</code> (<code>/#/profile</code>) — личный кабинет, смена пароля, загрузка аватара.</li>
  <li><code>AddressCreateComponent</code>, <code>PaymentMethodComponent</code> — управление адресной книгой и банковскими картами.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело запроса / Ответа</th></tr>
  </thead>
  <tbody>
    <tr><td>POST</td><td><code>/api/Users/</code></td><td>Регистрация пользователя</td><td><code>{ email, password, passwordRepeat, securityQuestion, securityAnswer }</code></td></tr>
    <tr><td>POST</td><td><code>/rest/user/login</code></td><td>Вход в систему</td><td><code>{ email, password }</code> ➔ <code>{ authentication: { token, bid, umail } }</code></td></tr>
    <tr><td>POST</td><td><code>/rest/user/reset-password</code></td><td>Сброс пароля</td><td><code>{ email, answer, newPassword, repeatNewPassword }</code></td></tr>
    <tr><td>GET / POST</td><td><code>/api/Addresss/</code></td><td>Список / Добавление адресов</td><td>Требует Bearer Token</td></tr>
    <tr><td>GET / POST</td><td><code>/api/Cards/</code></td><td>Список / Добавление платежных карт</td><td>Требует Bearer Token</td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Регистрация:</strong> Проверка формата email по RFC 5322. Запрет отправки формы с незаполненными обязательными полями. Валидация совпадения пароля и повторного пароля.</li>
  <li><strong>Аутентификация:</strong> Сохранение JWT токена в <code>localStorage</code> (ключ <code>token</code>). Применение токена через HTTP-интерцептор во всех последующих защищенных запросах.</li>
  <li><strong>Восстановление пароля:</strong> Динамическая подгрузка текста контрольного вопроса по введенному email. При неверном ответе выдача ошибки без раскрытия внутренней структуры данных.</li>
  <li><strong>Адресная книга:</strong> Возможность добавления нескольких адресов доставки с указанием страны, ФИО получателя, мобильного телефона, индекса, адреса и города.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Успешная регистрация нового клиента
  Given гость открывает страницу "/#/register"
  When заполняет email "client@test.com", пароль "Secret123!", подтверждение "Secret123!"
  And выбирает секретный вопрос "Your eldest siblings middle name?" и вводит ответ "Alexander"
  And нажимает кнопку "Register"
  Then система отображает нотификацию "Registration completed successfully. You can now log in."
  And пользователь перенаправляется на форму "/#/login"

Scenario: Ошибка при попытке входа с неверным паролем
  Given пользователь находится на "/#/login"
  When вводит валидный email и неверный пароль
  And нажимает "Log in"
  Then отображается сообщение "Invalid email or password."
  And JWT-токен не сохраняется в хранилище браузера</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Безопасность:</strong> Хранение паролей в хешированном виде с алгоритмом HMAC-SHA256 / bcrypt. Маскирование номеров кредитных карт (отображение только последних 4 цифр).</li>
  <li><strong>Производительность:</strong> Время генерации JWT и ответа API входа не более 200 мс.</li>
</ul>
`
  },
  {
    title: 'JS-4: Модуль каталога товаров, карточек продуктов и поисковой фильтрации',
    jiraKey: 'JS-4',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-4"><strong>JS-4</strong>: Модуль каталога товаров, карточек продуктов и поисковой фильтрации</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>High</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как покупатель магазина Juice Shop,<br/>
Я хочу просматривать витрину напитков и мерча, выполнять поиск в режиме реального времени и изучать детальную информацию о товарах,<br/>
Чтобы быстро находить интересующие продукты и принимать решение о покупке.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-CAT-01:</strong> Каталог доступен как авторизованным, так и неавторизованным пользователям.</li>
  <li><strong>BR-CAT-02:</strong> Товары выводятся плиткой с адаптивной сеткой (от 1 колонки на мобильных до 4-5 на Desktop).</li>
  <li><strong>BR-CAT-03:</strong> Поиск выполняется по наименованию и описанию товара без учета регистра.</li>
  <li><strong>BR-CAT-04:</strong> При нулевом остатке на складе кнопка добавления в корзину деактивируется с бейджем "Sold Out".</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>SearchResultComponent</code> (<code>/#/search</code>) — главный экран витрины, сетка товаров, контроллер пагинации.</li>
  <li><code>ProductDetailsComponent</code> (диалоговое окно Angular Material) — подробная информация о выбранном товаре, увеличенное фото, отзывы.</li>
  <li><code>NavbarComponent</code> — глобальная строка поиска (поисковый инпут с debounce 300ms).</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Параметры</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/rest/products/search</code></td><td>Поиск и получение товаров каталога</td><td>Query param <code>q</code> (поисковая строка)</td></tr>
    <tr><td>GET</td><td><code>/api/Products/:id</code></td><td>Получение детальной информации о товаре</td><td>Path param <code>id</code></td></tr>
    <tr><td>GET</td><td><code>/rest/products/:id/reviews</code></td><td>Получение отзывов к товару</td><td>Path param <code>id</code></td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Отображение карточки:</strong> Фотография товара, наименование, цена в валюте приложения, краткое описание (с многоточием при превышении длины), кнопка "Add to Basket".</li>
  <li><strong>Пагинация:</strong> Селектор количества отображаемых позиций (12, 24, 36 или 48), кнопки переключения страниц ("Next", "Previous", "First", "Last").</li>
  <li><strong>Живой поиск:</strong> Автоматическая фильтрация каталога при вводе символов без необходимости нажатия Enter. Кнопка очистки строки поиска (крестик).</li>
  <li><strong>Детальное модальное окно:</strong> Вызов окна при клике на изображение или название продукта; закрытие по Esc, клику вне окна или кнопке "Close".</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Поиск товаров по вхождению строки
  Given пользователь открыл витрину каталога
  When вводит в поисковую строку "Apple"
  Then в каталоге отображаются только товары, содержащие "Apple" (например, Apple Juice, Apple Pomace)
  And отображается счетчик найденных позиций

Scenario: Открытие детальной карточки продукта
  Given в каталоге отображается товар "Orange Juice"
  When пользователь кликает по карточке товара
  Then открывается модальное окно с детальным описанием, ценой и блоком отзывов</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>UI/UX:</strong> Плавные анимации появления карточек при смене страниц пагинации.</li>
  <li><strong>Оптимизация:</strong> Отложенная загрузка изображений (Lazy Loading).</li>
  <li><strong>Безопасность:</strong> Корректное экранирование поисковой строки для предотвращения DOM/Reflected XSS.</li>
</ul>
`
  },
  {
    title: 'JS-5: Модуль корзины покупателя (Shopping Basket) и промо-акций',
    jiraKey: 'JS-5',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-5"><strong>JS-5</strong>: Модуль корзины покупателя (Shopping Basket) и промо-акций</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>High</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как покупатель интернет-магазина,<br/>
Я хочу добавлять выбранные товары в корзину, изменять их количество, видеть итоговую сумму и применять скидочные купоны,<br/>
Чтобы сформировать состав заказа перед переходом к оплате.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-BSK-01:</strong> У каждого авторизованного пользователя есть индивидуальная корзина (BasketId).</li>
  <li><strong>BR-BSK-02:</strong> При добавлении одного и того же товара повторно увеличивается количество единиц (Quantity).</li>
  <li><strong>BR-BSK-03:</strong> Итоговая цена пересчитывается мгновенно по формуле: <code>Total = Sum(ItemPrice * Quantity) - Discount</code>.</li>
  <li><strong>BR-BSK-04:</strong> Промокоды проверяются на срок действия и однократность использования.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>BasketComponent</code> (<code>/#/basket</code>) — экран просмотра и редактирования корзины.</li>
  <li><code>NavbarComponent</code> — бейдж счетчика товаров в корзине в шапке сайта.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело запроса</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/rest/basket/:id</code></td><td>Получение содержимого корзины</td><td>Path param <code>id</code> (BasketId)</td></tr>
    <tr><td>POST</td><td><code>/api/BasketItems/</code></td><td>Добавление товара в корзину</td><td><code>{ ProductId, BasketId, quantity }</code></td></tr>
    <tr><td>PUT</td><td><code>/api/BasketItems/:id</code></td><td>Обновление количества товара</td><td><code>{ quantity }</code></td></tr>
    <tr><td>DELETE</td><td><code>/api/BasketItems/:id</code></td><td>Удаление товара из корзины</td><td>-</td></tr>
    <tr><td>PUT</td><td><code>/rest/basket/:id/coupon/:coupon</code></td><td>Применение скидочного купона</td><td>Path params</td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Индикатор в шапке:</strong> Отображение иконки тележки с цифровым бейджем общего числа единиц товара. Мгновенное обновление счетчика без перезагрузки страницы при добавлении товара.</li>
  <li><strong>Управление количеством:</strong> Кнопки "+" и "-" для каждой строки товара. При нажатии "-" на значении 1 количество не уходит в ноль (для удаления используется отдельная кнопка корзины).</li>
  <li><strong>Удаление позиций:</strong> Кнопка с иконкой мусорной корзины напротив каждого товара. При клике строка удаляется, сумма пересчитывается.</li>
  <li><strong>Кнопка Checkout:</strong> Кнопка перехода к оформлению заказа активна только в случае, если в корзине присутствует хотя бы один товар.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Увеличение количества товара в корзине
  Given у авторизованного пользователя в корзине лежит 1 шт. "Lemon Juice" по цене 2.50
  When пользователь нажимает кнопку "+" на строке товара
  Then количество товара становится равным 2
  And промежуточная сумма по позиции обновляется на 5.00
  And общая стоимость заказа пересчитывается автоматически

Scenario: Применение валидного скидочного купона
  Given пользователь находится на экране корзины с заказом на 10.00
  When вводит промокод на скидку 10% и нажимает "Apply"
  Then система отображает примененную скидку 1.00
  And итоговая цена к оплате составляет 9.00</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Синхронизация:</strong> Состояние корзины сохраняется в БД; при обновлении страницы или входе с другого устройства данные не теряются.</li>
  <li><strong>Консистентность:</strong> Атомарное обновление элементов корзины с защитой от состояния гонки (Race Condition).</li>
</ul>
`
  },
  {
    title: 'JS-6: Модуль оформления заказа, выбора доставки и проведения платежа (Checkout Flow)',
    jiraKey: 'JS-6',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-6"><strong>JS-6</strong>: Модуль оформления заказа, выбора доставки и проведения платежа (Checkout Flow)</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>Critical</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как клиент с сформированной корзиной,<br/>
Я хочу пройти пошаговый мастер оформления заказа: выбрать адрес, способ доставки и способ оплаты, а затем подтвердить заказ,<br/>
Чтобы успешно оплатить покупку и получить электронный инвойс.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-CHK-01:</strong> Оформление заказа доступно строго авторизованным клиентам с непустой корзиной.</li>
  <li><strong>BR-CHK-02:</strong> Доступно 3 тарифа доставки: One Day Delivery (0 дней, повышенный тариф), Fast Delivery (1-3 дня, средний тариф), Standard Delivery (3-5 дней, базовый тариф).</li>
  <li><strong>BR-CHK-03:</strong> После нажатия "Pay and Order" корзина очищается, заказу присваивается уникальный номер (Order ID).</li>
  <li><strong>BR-CHK-04:</strong> Пользователь имеет право скачать сформированный PDF-инвойс на странице подтверждения и в личном кабинете.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>AddressSelectComponent</code> (<code>/#/address/select</code>) — выбор адреса получателя из сохраненных.</li>
  <li><code>DeliveryMethodComponent</code> (<code>/#/delivery-method</code>) — выбор скорости доставки.</li>
  <li><code>PaymentComponent</code> (<code>/#/payment/shop</code>) — выбор платежной карты.</li>
  <li><code>OrderSummaryComponent</code> (<code>/#/order-summary</code>) — финальная сводная таблица параметров заказа.</li>
  <li><code>OrderCompletionComponent</code> (<code>/#/order-completion/:id</code>) — страница успеха с номером заказа и загрузкой PDF.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело / Ответ</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/api/Deliverys</code></td><td>Получение списка доступных тарифов доставки</td><td>-</td></tr>
    <tr><td>POST</td><td><code>/rest/basket/:id/checkout</code></td><td>Создание и финализация заказа</td><td><code>{ orderId, deliveryMethodId, addressId, paymentId }</code></td></tr>
    <tr><td>GET</td><td><code>/ftp/order_:id.pdf</code></td><td>Загрузка PDF счета-фактуры</td><td>PDF Binary stream</td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Мастер оформления (Wizard):</strong> Шаги с индикацией прогресса (Address ➔ Delivery ➔ Payment ➔ Summary). Невозможность перехода к следующему шагу без завершения предыдущего.</li>
  <li><strong>Order Summary:</strong> Детальная сводка с отображением: адрес доставки, метод доставки, субтотал товаров, стоимость доставки, примененная скидка, итоговая сумма.</li>
  <li><strong>Генерация инвойса:</strong> Формирование серверного PDF-документа с реквизитами магазина, датой заказа, списком позиций и QR-кодом подтверждения.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Сквозной успешный процесс оформления заказа
  Given авторизованный клиент нажал "Checkout" в корзине с товарами
  When выбирает сохраненный адрес доставки и нажимает "Continue"
  And выбирает "Standard Delivery (+2.00)" и нажимает "Continue"
  And выбирает банковскую карту "**** **** **** 1234" и нажимает "Continue"
  And проверяет итоговые данные на экране Order Summary и нажимает "Pay and Order"
  Then открывается страница подтверждения заказа с уникальным номером заказа
  And корзина пользователя очищается (счетчик в шапке становится 0)
  And доступна активная ссылка для скачивания PDF инвойса</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>PCI-DSS Соответствие:</strong> Запрет логирования и сохранения CVV кодов в постоянных хранилищах.</li>
  <li><strong>Идемпотентность:</strong> Защита от дублирования заказов при повторном клике кнопки отправки (Debounce / Disabling кнопки во время запроса).</li>
</ul>
`
  },
  {
    title: 'JS-7: Модуль отзывов о товарах и формы обратной связи (Feedback & Reviews)',
    jiraKey: 'JS-7',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-7"><strong>JS-7</strong>: Модуль отзывов о товарах и формы обратной связи (Feedback &amp; Reviews)</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>Medium</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как покупатель,<br/>
Я хочу оставлять оценки и текстовые отзывы к купленным товарам, а также направлять отзывы о работе магазина через форму обратной связи,<br/>
Чтобы делиться впечатлениями и помогать другим пользователям с выбором.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-REV-01:</strong> Отзывы к товарам могут публиковать только авторизованные клиенты.</li>
  <li><strong>BR-REV-02:</strong> Пользователь имеет право редактировать текст своего ранее оставленного отзыва.</li>
  <li><strong>BR-REV-03:</strong> Форма общей обратной связи (Customer Feedback) доступна всем посетителям и защищена математической капчей.</li>
  <li><strong>BR-REV-04:</strong> Рейтинг в форме обратной связи выставляется слайдером по шкале от 1 до 5 звезд.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>ProductDetailsComponent</code> — секция отзывов в модальном окне продукта, форма ввода нового отзыва, счетчик лайков.</li>
  <li><code>FeedbackComponent</code> (<code>/#/contact</code>) — форма обращения в компанию: поле комментария, слайдер рейтинга (1–5), поле решения капчи.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело запроса</th></tr>
  </thead>
  <tbody>
    <tr><td>PUT</td><td><code>/rest/products/:id/reviews</code></td><td>Добавление отзыва к товару</td><td><code>{ message, author }</code></td></tr>
    <tr><td>PATCH</td><td><code>/rest/products/reviews</code></td><td>Редактирование своего отзыва</td><td><code>{ id, message }</code></td></tr>
    <tr><td>POST</td><td><code>/rest/products/reviews/like</code></td><td>Поставить лайк отзыву</td><td><code>{ id }</code></td></tr>
    <tr><td>GET</td><td><code>/rest/captcha/</code></td><td>Получение математической капчи</td><td>Возвращает <code>{ captchaId, captcha }</code></td></tr>
    <tr><td>POST</td><td><code>/api/Feedbacks/</code></td><td>Отправка формы Feedback</td><td><code>{ comment, rating, captchaId, captcha }</code></td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Отзывы к продуктам:</strong> Текстовое поле ввода (макс. 500 знаков). После отправки отзыв мгновенно появляется в списке с указанием email автора и даты публикации.</li>
  <li><strong>Лайки:</strong> Счетчик полезности отзыва. Пользователь может проголосовать за отзыв один раз за сессию.</li>
  <li><strong>Капча:</strong> Динамический математический пример (например, 7 * 4 - 3 = ?). Форма Feedback не отправляется при неверном решении примера.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Публикация нового отзыва к товару
  Given авторизованный пользователь открыл карточку "Banana Juice"
  When пишет текст "Отличный сок, быстрая доставка!" и нажимает "Submit Review"
  Then отзыв появляется в списке отзывов к товару
  And поле ввода отзыва очищается

Scenario: Отправка общей обратной связи с неверной капчей
  Given посетитель открыл страницу "/#/contact"
  When вводит комментарий, выбирает рейтинг 5 и вводит неверный ответ на капчу
  And нажимает "Submit"
  Then система отображает ошибку "Invalid CAPTCHA code"
  And отзыв не сохраняется в базе данных</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Безопасность:</strong> Очистка и санитизация HTML тегов от Stored XSS атак при выводе отзывов других пользователей.</li>
  <li><strong>Производительность:</strong> Пагинация или виртуальный скроллинг при наличии более 50 отзывов у одного продукта.</li>
</ul>
`
  },
  {
    title: 'JS-8: Модуль виртуального ассистента поддержки клиентов (Chatbot "Juicy")',
    jiraKey: 'JS-8',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-8"><strong>JS-8</strong>: Модуль виртуального ассистента поддержки клиентов (Chatbot "Juicy")</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>Medium</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как клиент магазина Juice Shop,<br/>
Я хочу взаимодействовать с интерактивным чат-ботом поддержки "Juicy" в режиме реального времени,<br/>
Чтобы оперативно получать ответы на частые вопросы (FAQ), проверять статус моих заказов и условия акций без ожидания оператора.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-BOT-01:</strong> Чат-бот доступен через иконку саппорта в навигационной панели (<code>/#/chatbot</code>).</li>
  <li><strong>BR-BOT-02:</strong> Бот распознает ключевые намерения пользователя (Intent): проверка заказа, информация о купонах, контакты магазина, возврат товара.</li>
  <li><strong>BR-BOT-03:</strong> Для авторизованных пользователей бот обращается по имени/email и может предоставить статус последнего заказа.</li>
  <li><strong>BR-BOT-04:</strong> При неизвестном запросе бот предлагает список подсказок и стандартных тем.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>ChatbotComponent</code> (<code>/#/chatbot</code>) — диалоговое окно чата с облачками сообщений, индикатором набора текста ботом ("Juicy is typing...") и полем ввода.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Тело запроса</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/rest/chatbot/status</code></td><td>Проверка доступности сервиса чат-бота</td><td>-</td></tr>
    <tr><td>POST</td><td><code>/rest/chatbot/respond</code></td><td>Отправка сообщения пользователя боту</td><td><code>{ action: 'query', query: string }</code></td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Интерфейс чата:</strong> Разделение сообщений на "Пользователь" (справа) и "Juicy" (слева с аватаром бота). Автоскролл к последнему сообщению.</li>
  <li><strong>Обработка запросов:</strong> Поиск ключевых слов в запросе пользователя с использованием regex/NLP правил на стороне сервера.</li>
  <li><strong>Персонализация:</strong> Выдача информации о заказах только при наличии валидного JWT токена текущего пользователя.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Запрос информации о статусе заказа у чат-бота
  Given авторизованный пользователь перешел в чат-бот "/#/chatbot"
  When пишет сообщение "Where is my order?"
  Then бот отвечает: "Your order #[ID] is currently being delivered to your address."

Scenario: Запрос неизвестной команды
  Given пользователь пишет в чат бессмысленный набор символов "asdkasld123"
  Then бот вежливо отвечает, что не понял вопрос, и предлагает варианты: "You can ask me about orders, coupons, or products."</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Скорость отклика:</strong> Ответ бота возвращается не более чем за 800 мс.</li>
  <li><strong>Безопасность:</strong> Санитизация входящих сообщений во избежание Command Injection и XSS.</li>
</ul>
`
  },
  {
    title: 'JS-9: Модуль администрирования пользователей и мониторинга заказов (Admin Panel)',
    jiraKey: 'JS-9',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-9"><strong>JS-9</strong>: Модуль администрирования пользователей и мониторинга заказов (Admin Panel)</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>High</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как администратор платформы Juice Shop,<br/>
Я хочу иметь панель управления для мониторинга активности пользователей, просмотра журнала заказов и управления учетными записями,<br/>
Чтобы контролировать бизнес-показатели магазина и обеспечивать бесперебойную операционную деятельность.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-ADM-01:</strong> Доступ к разделу строго ограничен ролью <code>admin</code> (проверка прав в JWT токене и на сервере).</li>
  <li><strong>BR-ADM-02:</strong> Пользователям с ролью <code>customer</code> или неавторизованным гостям доступ блокируется с ошибкой 403 Forbidden.</li>
  <li><strong>BR-ADM-03:</strong> Администратор может просматривать список учетных записей, их роли, статус и даты создания.</li>
  <li><strong>BR-ADM-04:</strong> Администратор имеет доступ к полному журналу заказов всех клиентов.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>AdministrationComponent</code> (<code>/#/administration</code>) — консоль администратора, таблицы пользователей и заказов.</li>
  <li><code>AdminGuard</code> (Angular Route Guard) — перехват перехода на роут при отсутствии административных прав.</li>
</ul>

<h3>3.2. REST API эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Метод</th><th>Эндпоинт</th><th>Описание</th><th>Требования доступа</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/api/Users/</code></td><td>Получение полного списка пользователей</td><td>Role: admin</td></tr>
    <tr><td>DELETE</td><td><code>/api/Users/:id</code></td><td>Удаление пользователя</td><td>Role: admin</td></tr>
    <tr><td>GET</td><td><code>/rest/order-history</code></td><td>Просмотр истории заказов всех клиентов</td><td>Role: admin</td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Таблица пользователей:</strong> Отображение столбцов ID, Email, Role, CreatedAt. Возможность поиска и фильтрации по email.</li>
  <li><strong>Удаление пользователя:</strong> Кнопка удаления с диалоговым окном подтверждения ("Are you sure?").</li>
  <li><strong>Безопасность ролевой модели:</strong> Любой запрос к <code>/api/Users/</code> без валидного токена администратора должен отклоняться на уровне бэкенд-мидлвара.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Попытка несанкционированного доступа обычного пользователя
  Given клиент авторизован под обычной учетной записью с ролью "customer"
  When пытается напрямую открыть URL "/#/administration"
  Then система перенаправляет его на главную страницу или страницу 403
  And данные пользователей не отображаются

Scenario: Успешная работа администратора в консоли
  Given пользователь авторизован под учетной записью администратора ("admin@juice-sh.op")
  When открывает раздел "/#/administration"
  Then отображается таблица со всеми пользователями системы и кнопки управления</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Аудит безопасности:</strong> Логирование попыток несанкционированного доступа (BOLA / Broken Function Level Authorization).</li>
  <li><strong>Производительность:</strong> Пагинация серверных данных при количестве пользователей более 100.</li>
</ul>
`
  },
  {
    title: 'JS-10: Модуль интерактивной доски заданий и геймификации (Score Board & Challenges)',
    jiraKey: 'JS-10',
    content: `
<h2>1. Паспорт функционального модуля</h2>
<table>
  <tr><th>Параметр</th><th>Значение</th></tr>
  <tr><td>Задача в Jira</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-10"><strong>JS-10</strong>: Модуль интерактивной доски заданий и геймификации (Score Board &amp; Challenges)</a></td></tr>
  <tr><td>Родительский Эпик</td><td><a href="https://romeo-timony.atlassian.net/browse/JS-1"><strong>JS-1</strong>: Разработка ключевых функциональных модулей</a></td></tr>
  <tr><td>Приоритет</td><td>Medium</td></tr>
  <tr><td>Статус аналитики</td><td>Ready for Dev &amp; QA</td></tr>
</table>

<h2>2. Бизнес-контекст и User Story</h2>
<p><strong>User Story:</strong><br/>
<em>Как обучающийся специалист по кибербезопасности или разработчик,<br/>
Я хочу использовать интерактивную доску заданий (Score Board) с фильтрацией по категориям и уровню сложности,<br/>
Чтобы отслеживать прогресс выполнения практических заданий и получать мгновенные подтверждения успешного решения.</em></p>

<h3>Бизнес-правила (Business Rules):</h3>
<ul>
  <li><strong>BR-SCR-01:</strong> Доска заданий расположена по адресу <code>/#/score-board</code>.</li>
  <li><strong>BR-SCR-02:</strong> Задания делятся по уровням сложности (от 1 до 6 звезд) и категориям уязвимостей (XSS, Injection, Broken Auth и др.).</li>
  <li><strong>BR-SCR-03:</strong> При решении задания на экране появляется всплывающее уведомление (Toast / Notification) со звуковым эффектом и конфетти.</li>
  <li><strong>BR-SCR-04:</strong> Статус задания меняется с "Unsolved" (красный бейдж) на "Solved" (зеленый бейдж) с сохранением состояния.</li>
</ul>

<h2>3. Системный анализ и архитектурные решения</h2>
<h3>3.1. Frontend компоненты (Angular):</h3>
<ul>
  <li><code>ScoreBoardComponent</code> (<code>/#/score-board</code>) — витрина челленджей, фильтры по категориям и звездам, общий прогресс-бар.</li>
  <li><code>ChallengeService</code> — сервис получения списка вызовов и прослушивания событий выполнения.</li>
  <li><code>ChallengeStatusBadgeComponent</code> — бейдж статуса ("Solved" / "Unsolved").</li>
</ul>

<h3>3.2. REST API &amp; WebSocket эндпоинты:</h3>
<table>
  <thead>
    <tr><th>Протокол</th><th>Эндпоинт</th><th>Описание</th></tr>
  </thead>
  <tbody>
    <tr><td>GET</td><td><code>/api/Challenges/</code></td><td>Получение полного списка испытаний, категорий, описаний и подсказок</td></tr>
    <tr><td>WebSocket / Polling</td><td><code>/socket.io/</code></td><td>Событие <code>challenge solved</code> с метаданными решенного задания</td></tr>
  </tbody>
</table>

<h2>4. Функциональные требования (FR)</h2>
<ol>
  <li><strong>Фильтрация:</strong> Мультиселект по категориям (Injection, XSS, Security Misconfiguration и т.д.) и кнопка выбора уровня сложности (1-6 звезд).</li>
  <li><strong>Прогресс-бар:</strong> Отображение процента и счетчика решенных задач (например, "15 / 105 solved - 14%").</li>
  <li><strong>Подсказки (Hints):</strong> Иконка лампочки для каждого задания с раскрывающейся ссылкой на документацию или туториал.</li>
</ol>

<h2>5. Критерии приемки (BDD / Gherkin)</h2>
<pre><code>Scenario: Фильтрация заданий по уровню сложности
  Given пользователь открыл Score Board "/#/score-board"
  When выбирает фильтр сложности "1 Star"
  Then в таблице отображаются только задания начального уровня сложности
  And счетчик отображает количество заданий выбранного уровня

Scenario: Получение нотификации о решении задания
  Given пользователь выполнил целевое действие задания (например, зашел на скрытый роут)
  When сервер фиксирует прохождение испытания
  Then на экране немедленно отображается баннер "You solved a challenge: Score Board!"
  And в таблице задание помечается как решенное</code></pre>

<h2>6. Нефункциональные требования (NFR)</h2>
<ul>
  <li><strong>Персистентность:</strong> Сохранение прогресса решения заданий в базе данных приложения и синхронизация при перезагрузке страницы.</li>
  <li><strong>Производительность:</strong> Быстрый рендеринг таблицы челленджей (более 100 позиций) без задержек интерфейса.</li>
</ul>
`
  }
];

(async () => {
  try {
    console.log('1. Creating parent Epic page in Confluence...');
    const epicPage = await createPage(
      'Эпик JS-1: Разработка ключевых функциональных модулей веб-приложения OWASP Juice Shop',
      epicContent,
      homePageId
    );
    console.log(`Created Epic page in Confluence: ID=${epicPage.id}, Title="${epicPage.title}"`);

    console.log(`\n2. Creating 8 module pages under Epic page ID ${epicPage.id}...`);
    for (let i = 0; i < modulePages.length; i++) {
      const mod = modulePages[i];
      try {
        const page = await createPage(mod.title, mod.content, epicPage.id);
        console.log(`[${i + 1}/${modulePages.length}] Created Confluence page: ID=${page.id}, Jira=${mod.jiraKey}, Title="${page.title}"`);
      } catch (err) {
        console.error(`Failed to create page "${mod.title}":`, err.message);
      }
    }

    console.log('\nAll Confluence pages created successfully!');
  } catch (err) {
    console.error('Error during execution:', err);
  }
})();
