import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchConfig, updateConfig, type BotConfig } from './client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

const sampleConfig: BotConfig = {
  LOG_CHANNEL_ID: '500',
  SPAM_EXCEPTION_CHANNELS: ['600'],
  TEMPBAN_CHANNEL_ID: '',
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

describe('config API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchConfig GETs the current config', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(sampleConfig))
    const result = await fetchConfig()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/config')
    expect(result).toEqual(sampleConfig)
  })

  it('updateConfig PUTs the full config and returns the saved result', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(sampleConfig))
    const result = await updateConfig(sampleConfig)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/config')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(sampleConfig)
    expect(result).toEqual(sampleConfig)
  })
})
