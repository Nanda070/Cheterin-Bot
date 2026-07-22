import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EMPTY_BOT_CONFIG } from '../config/botConfigDefaults'
import { renderWithI18n } from '../test/renderWithI18n'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'

describe('ModuleConfigPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders moderation config fields', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(EMPTY_BOT_CONFIG)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithI18n(<ModuleConfigPanel variant="moderation" title="Модерация и спам" />)

    expect(await screen.findByLabelText('Канал логов')).toBeInTheDocument()
  })

  it('saves updated config', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(EMPTY_BOT_CONFIG)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'logs' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateConfig').mockResolvedValue(EMPTY_BOT_CONFIG)

    renderWithI18n(<ModuleConfigPanel variant="moderation" />)

    await waitFor(() => screen.getByLabelText('Канал логов'))
    fireEvent.click(screen.getByLabelText('Канал логов'))
    fireEvent.click(await screen.findByRole('option', { name: 'logs' }))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ LOG_CHANNEL_ID: '500' })),
    )
  })
})
