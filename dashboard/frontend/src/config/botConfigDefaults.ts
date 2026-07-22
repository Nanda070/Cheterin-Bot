import type { BotConfig } from '../api/client'

export const EMPTY_BOT_CONFIG: BotConfig = {
  LOG_CHANNEL_ID: '',
  SPAM_EXCEPTION_CHANNELS: [],
  TEMPBAN_CHANNEL_ID: '',
  TEMPBAN_LOG_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  BUTTON_WEBHOOK_USERNAME: '',
  BUTTON_WEBHOOK_AVATAR_URL: '',
  SERVER_INVITE_LINK: '',
  VOICE_LOBBY_CHANNEL_ID: '',
  VOICE_PANEL_CHANNEL_ID: '',
  VOICE_LOG_CHANNEL_ID: '',
  VOICE_PANEL_THUMB_URL: '',
  SUPPLY_ROLE_ID: '',
  SUPPLY_VOICE_CHANNEL_ID: '',
  SUPPLY_LOG_CHANNEL_ID: '',
  SUPPLY_REMINDER_MINUTES: '',
}

export type ModuleConfigVariant =
  | 'moderation'
  | 'antispam'
  | 'tempban'
  | 'welcome-onboarding'
  | 'buttons'
  | 'voice'
  | 'supply'
