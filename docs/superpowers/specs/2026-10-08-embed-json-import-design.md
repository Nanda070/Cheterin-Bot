# Embed Builder: импорт/экспорт JSON, несколько embed'ов, подстановки

Дата: 2026-10-08
Страница: `/reaction-roles?tab=embeds` (`dashboard/frontend/src/pages/EmbedBuilder.tsx`)

## Цель

Администратор вставляет JSON (в стиле discohook.app или собственную библиотеку
сообщений) и получает готовое сообщение в форме и превью, которое бот отправляет
в канал. Сообщение может содержать до 10 embed'ов. Текущее сообщение можно
выгрузить обратно в JSON.

Критерии успеха:

1. JSON из Discohook (`{content, embeds:[…]}`) применяется одной кнопкой, форма и
   превью показывают все embed'ы, отправка создаёт одно сообщение в Discord.
2. Библиотека из 49 ивентов (массив `{category, score, event, embed:{plainText,…}}`)
   применяется без правок: появляется список с поиском, клик загружает ивент в форму.
3. Весь список сохраняется в шаблоны одной кнопкой.
4. `{DateNow}`, `{Channel}`, `{Eventer}` заполняются в полях подстановки и
   попадают в превью и в отправленное сообщение.
5. Существующие шаблоны и старые клиенты API (поле `embed`) продолжают работать.

## Вне объёма

- `username` / `avatar_url` (бот не вебхук), вложения, кнопки-ссылки из JSON.
- Несколько embed'ов для welcome / feedback / events — они остаются на одном.
- Массовая отправка всех сообщений списка в канал.
- Подстановка плейсхолдеров на стороне бота; смысл полей `category` / `score`.
- Перестановка embed'ов мышью (порядок меняется через JSON).

## Контракт API

Везде, где сейчас `embed: EmbedSpec`, появляется `embeds: EmbedSpec[]`.

| Маршрут | Изменение |
|---|---|
| `POST /api/embed-messages`, `PUT /api/embed-messages/{c}/{m}` | Принимают `embeds` (0–10). Если `embeds` нет — читают старое `embed` как `[embed]`. |
| `GET /api/embed-messages/{c}/{m}` | Отдаёт `embeds` (все embed'ы сообщения) и `embed` (первый, для совместимости). |
| `GET /api/embed-templates` | Каждый шаблон отдаёт `embeds` и `embed` (первый). |
| `POST /api/embed-templates` | Принимает `embeds` либо старое `embed`. |
| `POST /api/embed-templates/bulk` | **Новый.** Тело `{templates: [{name, content, embeds}]}`, до 200 штук. Ответ `{created: Template[], skipped: [{name, reason}]}`. |

Пустые spec'и (без title/description/fields/image/thumbnail) бэкенд отбрасывает
перед валидацией и отправкой.

Новые коды ошибок (HTTP 400): `too_many_embeds` (больше 10), `v2_too_large`
(см. Components V2). `embed_too_large` теперь считает сумму по всем embed'ам
сообщения — лимит Discord 6000 символов общий.

### Шаблоны

- Хранение: новые шаблоны пишутся с ключом `embeds`. Старые записи с `embed`
  читаются как `[embed]`, миграция данных не нужна.
- `MAX_TEMPLATES` поднимается с 50 до 200.
- Bulk: одна запись в `settings_db` на весь запрос. Имя обрезается до 60 символов.
  Пропуск с причиной: `duplicate_name` (имя уже есть на сервере или повторилось в
  запросе), `too_many_templates` (лимит исчерпан), `invalid_name`, либо код
  валидации embed'а. `role_ids` у bulk-шаблонов пустые.

## Формат JSON

Новый модуль `dashboard/frontend/src/utils/messageJson.ts` — чистые функции.

```ts
interface ImportedMessage { name: string; group: string; content: string; embeds: EmbedSpec[] }
type ParseResult =
  | { ok: true; messages: ImportedMessage[]; warnings: string[] }   // warnings — ключи i18n + параметры
  | { ok: false; error: string }

parseMessageJson(text: string): ParseResult
exportMessageJson(content: string, embeds: EmbedSpec[]): string
```

### Распознавание

Объект верхнего уровня классифицируется так (первое совпадение):

1. Есть массив `messages` → бэкап Discohook: каждое `messages[i].data` — сообщение.
2. Есть `embeds` (массив) или `content` → одно сообщение Discohook.
3. Есть объект `embed` → **обёртка** (формат библиотеки ивентов): одно сообщение
   с одним embed'ом. `content` = `embed.plainText` ?? `content` обёртки.
4. Есть любой из ключей `title`, `description`, `fields`, `author`, `footer`,
   `image`, `thumbnail` → голый embed: одно сообщение с одним embed'ом;
   `plainText` внутри → `content`.
5. Иначе — ошибка «не похоже на сообщение».

Массив верхнего уровня:

- Все элементы — голые embed'ы без `plainText`, и их ≤ 10 → **одно** сообщение с
  N embed'ами (как `embeds` в Discord).
- Иначе каждый элемент — отдельное сообщение по правилам выше. Элементы, которые
  не распознаны, пропускаются с предупреждением.

Имя сообщения: `event` → `name` → `title` обёртки → `title` embed'а →
`author.name` → «Сообщение N». `group` = `category` обёртки или пустая строка.

### Нормализация embed'а

- `color`: число → `#rrggbb`; строка `#rrggbb` / `rrggbb` принимается; иначе и при
  отсутствии — пустая строка (без цвета, а не дефолтный красный).
- `url`, `author.url`, `author.icon_url`, `footer.icon_url`, `timestamp`
  сохраняются, хотя отдельных полей в форме для части из них нет.
- `fields[]`: `name`, `value`, `inline`.

### Предупреждения и ошибки

- Предупреждение (не блокирует): игнорируемые ключи сообщения — `username`,
  `avatar_url`, `attachments` (непустой), `components` (непустой), `thread_name`,
  `flags`; embed'ов в одном сообщении больше 10 (лишние отброшены); пропущенные
  элементы массива.
- Ошибка (блокирует): невалидный JSON (с текстом ошибки парсера), верхний уровень
  не объект и не массив, ни одного распознанного сообщения.
- Метаданные обёртки (`category`, `score`, `event`) предупреждений не вызывают.

### Экспорт

Формат Discohook: `{ "content": string | null, "embeds": [...] | null, "attachments": [] }`.
`color` числом, пустые строки и пустые вложенные объекты опущены, отступ 2 пробела.
Экспортируется текст **без** применённых подстановок.

## Подстановки

Новый модуль `dashboard/frontend/src/utils/placeholders.ts`:

```ts
findPlaceholders(content: string, embeds: EmbedSpec[]): string[]            // уникальные, в порядке появления
applyPlaceholders(content, embeds, values: Record<string, string>): { content: string; embeds: EmbedSpec[] }
```

- Шаблон: `\{([A-Za-z_][A-Za-z0-9_]*)\}`. Упоминания `<@&id>` и эмодзи `<:n:id>`
  под него не попадают.
- Ищется и заменяется во всех строковых полях: content, title, description, url,
  author.*, footer.*, image.url, thumbnail.url, имена и значения полей.
- Пустое значение → плейсхолдер остаётся как есть.
- В UI под формой блок «Подстановки» с полем на каждый найденный плейсхолдер;
  блок скрыт, если ничего не найдено. Значения живут в состоянии страницы и
  сохраняются при переключении между сообщениями списка.
- Превью показывает результат подстановки. При отправке подстановка применяется
  к payload; валидация длины идёт по подставленному тексту.
- Шаблоны и экспорт JSON сохраняют исходный текст с `{…}`.
- Если при отправке остались незаполненные плейсхолдеры — подсказка рядом с
  кнопкой, отправку не блокирует.

## Интерфейс

Левая колонка `EmbedBuilder.tsx`, сверху вниз: режим → Components V2 → шаблоны →
**JSON** → канал → текст сообщения → **переключатель embed'ов** → поля embed'а →
**подстановки** → кнопки ролей → отправка.

Новые компоненты в `dashboard/frontend/src/components/`:

- `JsonImportPanel.tsx` — textarea; «Применить JSON»; «Скопировать JSON» (кладёт
  экспорт в textarea и в буфер обмена); ошибка и предупреждения под полем. Если
  сообщений больше одного — список: поиск по имени, строки «имя · группа», клик
  загружает сообщение в форму (текст и embed'ы заменяются, выбранные роли и
  канал остаются), активная строка подсвечена; кнопка «Сохранить все как
  шаблоны (N)» с итогом «создано X, пропущено Y». Одно сообщение загружается в
  форму сразу.
- `EmbedFieldsForm.tsx` — поля одного embed'а, вынесенные из `EmbedBuilder.tsx`
  без изменения набора полей.
- `PlaceholderInputs.tsx` — блок подстановок.

Переключатель embed'ов: кнопки «Embed 1…N», «+ Добавить» (до 10), «Удалить»
(минимум один слот остаётся; пустые слоты не отправляются).

`EmbedPreview.tsx` получает необязательный проп `embeds: EmbedSpec[]`; старый
`embed` остаётся для других страниц. Embed'ы идут столбиком под текстом.

Все новые строки — в `i18n/ru/community.ts` и `i18n/en/community.ts`.

## Бэкенд

`bot/core/embed_builder.py`:

- `specs_from_body(body) -> list[dict] | None` — `embeds` или `[embed]`, пустые
  отброшены; `None`, если `embeds` не список или элемент не объект.
- `validate_embed_specs(specs, content) -> str | None` — `too_many_embeds`,
  покомпонентные лимиты, общий лимит 6000, `empty_embed`.
- `message_to_editor_payload` — возвращает `embeds` (до 10) и `embed`.
- `save_templates_bulk(guild_id, items)`; `list_templates` / `save_template`
  работают с `embeds`.

`bot/core/components_v2.py`: `send_message`, `edit_message`, `build_layout_view`
получают необязательный `embeds: list[discord.Embed] | None`. Существующие
вызовы с `embed=` по всему боту не меняются. В V1 список уходит как `embeds=`.

### Components V2

V2-сообщение не может нести embed'ы, поэтому каждый embed → отдельный
`Container` со своим акцентным цветом. `content` — первым блоком первого
контейнера (как сейчас), кнопки ролей — в последнем.

Перед отправкой собранный layout проверяется: больше 40 компонентов или больше
4000 символов текста суммарно → 400 `v2_too_large` с понятным сообщением вместо
безликого `discord_error`.

Чтение V2-сообщения обратно в редактор: один spec на `Container` верхнего
уровня, best-effort, как сейчас для одного.

## Обработка ошибок

- Ошибки парсинга JSON показываются в панели JSON и не трогают форму.
- Ошибки API идут через существующий `formatApiError`; для `too_many_embeds` и
  `v2_too_large` добавляются переводы.
- Клиентская валидация (`validateEmbedSpecs`) повторяет серверную: количество,
  лимиты каждого embed'а, общий лимит 6000.

## Тесты

vitest:

- `messageJson.test.ts` — все пять форм объекта; массив голых embed'ов (≤10 →
  одно сообщение, >10 → список); массив обёрток с `plainText`/`event`/`category`
  (на реальном фрагменте библиотеки ивентов); цвет числом/строкой/отсутствует;
  предупреждения по игнорируемым ключам; ошибки; round-trip экспорт → импорт.
- `placeholders.test.ts` — поиск по всем полям, порядок и уникальность, пустое
  значение, упоминания и эмодзи не задеты.
- `embedUtils.test.ts` — `validateEmbedSpecs`: 11 embed'ов, суммарный лимит.

pytest (`dashboard/backend/tests/`):

- маршруты: создание/редактирование с `embeds`, со старым `embed`, 11 embed'ов,
  общий лимит 6000; `GET` сообщения с несколькими embed'ами;
- шаблоны: чтение старой записи с `embed`, сохранение с `embeds`, bulk
  (созданные, дубликаты, лимит);
- `components_v2`: контейнер на embed, цвета, кнопки в последнем, `v2_too_large`.

Проверка в браузере: вставить библиотеку из 49 ивентов, выбрать ивент, заполнить
подстановки, убедиться в превью; вставить Discohook-JSON с двумя embed'ами.
