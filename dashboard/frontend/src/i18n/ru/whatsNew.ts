import type { TranslationDict } from '../types'

const whatsNew: TranslationDict = {
  'whatsNew.title': 'Что нового',
  'whatsNew.subtitle': '{date}',
  'whatsNew.gotIt': 'Понятно',
  'whatsNew.item.embedJsonImport':
    'Embed Builder: вставьте JSON из Discohook или свою библиотеку сообщений — форма и превью заполнятся сами; текущее сообщение копируется как JSON',
  'whatsNew.item.embedMultiple':
    'До 10 эмбедов в одном сообщении — вкладки «Эмбед 1…N»; в Components V2 каждый эмбед идёт отдельным контейнером',
  'whatsNew.item.embedPlaceholders':
    'Подстановки: для {DateNow}, {Channel} и любых {Имя} появляются поля — значения подставляются в превью и при отправке',
  'whatsNew.item.embedBulkTemplates':
    'Библиотека сообщений из JSON: список с поиском и «Сохранить все как шаблоны»; лимит шаблонов — 200 на сервер',
}

export default whatsNew
