# Anti-Spam Cog

> 23 nodes

## Key Concepts

- **Spam** (13 connections) — `spam.py`
- **spam.py** (5 connections) — `spam.py`
- **.on_interaction()** (5 connections) — `spam.py`
- **._make_disabled_spam_view()** (5 connections) — `spam.py`
- **._punish()** (5 connections) — `spam.py`
- **.purge_recent_messages()** (5 connections) — `spam.py`
- **._handle_spam_ban()** (4 connections) — `spam.py`
- **._handle_spam_leave()** (4 connections) — `spam.py`
- **Interaction** (3 connections)
- **.on_message()** (3 connections) — `spam.py`
- **._cleanup_cache()** (2 connections) — `spam.py`
- **View** (2 connections)
- **Message** (2 connections)
- **setup()** (2 connections) — `spam.py`
- **.__init__()** (1 connections) — `spam.py`
- **.cog_unload()** (1 connections) — `spam.py`
- **._before_cleanup()** (1 connections) — `spam.py`
- **Guild** (1 connections)
- **Member** (1 connections)
- **Удаляет устаревшие записи из кэша спам-детектора.** (1 connections) — `spam.py`
- **Обработка кнопок спам-инцидентов — работает и после перезапуска бота.** (1 connections) — `spam.py`
- **Создаёт вью с отключёнными кнопками для обновления сообщения.** (1 connections) — `spam.py`
- **Удаляет сообщения участника за последние 20 минут во всех каналах и тредах.** (1 connections) — `spam.py`

## Relationships

- [Bot Config Store](Bot_Config_Store.md) (1 shared connections)
- [Moderation Routes](Moderation_Routes.md) (1 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)

## Source Files

- `spam.py`

## Audit Trail

- EXTRACTED: 69 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*