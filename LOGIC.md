# Lost & Found Bot — Логика работы

## Общее описание

Telegram-бот для публикации объявлений о потерянных и найденных вещах. Пользователь проходит пошаговый диалог (ConversationHandler), по итогу которого запись сохраняется в CSV-файл.

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Бот | `python-telegram-bot` (async) |
| Хранение данных | CSV-файлы (`database.py`) |
| Конфиг | `.env` → `BOT_TOKEN` |

---

## Команды

| Команда | Действие |
|---------|----------|
| `/start` | Начать новый диалог — выбор «потерял / нашёл» |
| `/cancel` | Отменить текущий диалог на любом шаге |
| `/help` | Справка по работе бота |

---

## Диалог (ConversationHandler)

Бот ведёт пользователя через 5 последовательных состояний:

```
/start
  │
  ▼
┌─────────────────────┐
│ 0. CHOOSING_TYPE    │  Inline-кнопки: "I Lost Something" / "I Found Something"
└────────┬────────────┘
         │ callback_data = "lost" | "found"
         ▼
┌─────────────────────┐
│ 1. CATEGORY         │  Reply-клавиатура с категориями (14 шт.)
└────────┬────────────┘
         │ текст кнопки → маппинг в чистое название через CATEGORY_MAP
         ▼
┌─────────────────────┐
│ 2. DESCRIPTION      │  Свободный текст — описание предмета
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 3. PHOTO            │  Отправка фото или «Skip Photo»
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 4. REWARD_OR_CONTACT│  Если lost → сумма вознаграждения или «No reward»
│                     │  Если found → контактные данные (телефон/email/username)
└────────┬────────────┘
         │
         ▼
    Сохранение в CSV
    Вывод сводки
    ConversationHandler.END
```

---

## Подробное описание каждого шага

### 0. CHOOSING_TYPE

- **Триггер:** `/start`
- **UI:** Inline-клавиатура с двумя кнопками
- **Данные:** `context.user_data['item_type']` = `"lost"` или `"found"`
- **Следующее состояние:** CATEGORY

### 1. CATEGORY

- **UI:** Reply-клавиатура 5 рядов (14 категорий с эмодзи)
- **Категории:** Toy, Phone, Laptop or Tablet, Bag or Bagpack, Wallet, Keys, Document, Clothing, Jewelry, Watches, Glasses or Sunglasses, Earphones or Earbuds, Pets, Other
- **Маппинг:** эмодзи-текст кнопки → чистое имя через `CATEGORY_MAP`
- **Данные:** `context.user_data['category']`
- **Следующее состояние:** DESCRIPTION

### 2. DESCRIPTION

- **UI:** свободный ввод текста
- **Подсказка:** цвет, размер, бренд, особые приметы
- **Данные:** `context.user_data['description']`
- **Следующее состояние:** PHOTO

### 3. PHOTO

- **UI:** ожидание фото или кнопка «Skip Photo»
- **Обработка:**
  - Фото получено → `photo_file_id = update.message.photo[-1].file_id`
  - Skip → `photo_file_id = None`
- **Следующее состояние:** REWARD_OR_CONTACT

### 4. REWARD_OR_CONTACT

- **Если `item_type == "lost"`:**
  - Запрос суммы вознаграждения или «No reward»
  - Данные: `context.user_data['reward']`
- **Если `item_type == "found"`:**
  - Запрос контактной информации (телефон, email, Telegram username)
  - Данные: `context.user_data['contact_info']`
- **Далее:** сохранение в CSV → сводка → END

---

## Хранение данных (CSV)

Данные хранятся в двух CSV-файлах. Файлы создаются автоматически при импорте `database.py`.

### Файл `lost_items.csv`

| Поле | Описание |
|------|----------|
| id | Автоинкремент |
| user_id | Telegram user ID |
| category | Категория предмета |
| description | Описание |
| photo_file_id | Telegram file_id фото (может быть пустым) |
| reward | Вознаграждение (может быть пустым) |
| created_at | ISO timestamp создания записи |

### Файл `found_items.csv`

| Поле | Описание |
|------|----------|
| id | Автоинкремент |
| user_id | Telegram user ID |
| category | Категория предмета |
| description | Описание |
| photo_file_id | Telegram file_id фото (может быть пустым) |
| contact_info | Контактные данные нашедшего (может быть пустым) |
| created_at | ISO timestamp создания записи |

### Функции (`database.py`)

| Функция | Назначение |
|---------|-----------|
| `init_database()` | Создаёт CSV-файлы с заголовками, если не существуют |
| `save_lost_item(...)` → `int` | Добавляет строку в `lost_items.csv`, возвращает ID |
| `save_found_item(...)` → `int` | Добавляет строку в `found_items.csv`, возвращает ID |
| `get_lost_items(limit)` → `list[dict]` | Последние N потерянных вещей |
| `get_found_items(limit)` → `list[dict]` | Последние N найденных вещей |

---

## Сводка (Summary)

После сохранения бот формирует сообщение-сводку, которое включает:

- Report ID (из CSV)
- Тип: Lost / Found
- Категория
- Описание (обрезается до 100 символов)
- Фото: есть / нет
- Reward (для lost) или Contact (для found, обрезается до 50 символов)

---

## Точка входа

```
main() →
  1. Читает BOT_TOKEN из .env
  2. Создаёт Application
  3. Регистрирует ConversationHandler (entry: /start, fallback: /cancel)
  4. Регистрирует /help
  5. Запускает polling
```
