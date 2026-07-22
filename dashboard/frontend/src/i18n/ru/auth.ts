import type { TranslationDict } from '../types'

const auth: TranslationDict = {
  'login.title': 'Панель управления',
  'login.subtitle': 'Войдите через Discord, чтобы получить доступ к панели модерации сервера.',
  'login.button': 'Войти через Discord',
  'login.feature.moderation': 'Модерация, анти-спам и Lockdown',
  'login.feature.supply': 'Сборы на поставку с резервом и напоминаниями',
  'login.feature.voice': 'Приватные голосовые комнаты',
  'login.footer': 'Доступ только для модераторов и администраторов сервера',

  'accessDenied.title': 'Доступ запрещён',
  'accessDenied.body':
    'У вашей учётной записи нет прав для просмотра этой панели. Доступ есть только у модераторов и администраторов сервера.',
  'accessDenied.back': 'Вернуться на страницу входа',

  'notFound.title': 'Страница не найдена',
  'notFound.body': 'Такого адреса не существует — возможно, ссылка устарела или в ней опечатка.',
  'notFound.back': 'Вернуться на главную',

  'leaderboard.title': 'Рейтинг участников',
  'leaderboard.subtitle': 'Топ-100 по опыту: активность в чатах и голосовых каналах.',
  'leaderboard.loading': 'Загрузка…',
  'leaderboard.empty': 'Рейтинг пока пуст.',
  'leaderboard.error': 'Рейтинг недоступен: система уровней или публичная страница отключены.',
  'leaderboard.levelShort': 'Ур. {level}',
  'leaderboard.xp': '{xp} XP',
  'leaderboard.guildSuffix': ' — {name}',
}

export default auth
