import type { TranslationDict } from '../types'

const auth: TranslationDict = {
  'login.title': 'Control panel',
  'login.subtitle': 'Sign in with Discord to access your server moderation panel.',
  'login.button': 'Sign in with Discord',
  'login.feature.moderation': 'Moderation, anti-spam, and lockdown',
  'login.feature.supply': 'Supply runs with reserve and reminders',
  'login.feature.voice': 'Private voice rooms',
  'login.footer': 'Access is limited to server moderators and administrators',

  'accessDenied.title': 'Access denied',
  'accessDenied.body':
    'Your account does not have permission to view this panel. Access is limited to server moderators and administrators.',
  'accessDenied.back': 'Back to sign in',

  'notFound.title': 'Page not found',
  'notFound.body': 'This URL does not exist — the link may be outdated or mistyped.',
  'notFound.back': 'Back to home',

  'leaderboard.title': 'Member ranking',
  'leaderboard.subtitle': 'Top 100 by XP: activity in text and voice channels.',
  'leaderboard.loading': 'Loading…',
  'leaderboard.empty': 'The leaderboard is empty.',
  'leaderboard.error': 'Leaderboard unavailable: level system or public page is disabled.',
  'leaderboard.levelShort': 'Lv. {level}',
  'leaderboard.xp': '{xp} XP',
  'leaderboard.guildSuffix': ' — {name}',
}

export default auth
