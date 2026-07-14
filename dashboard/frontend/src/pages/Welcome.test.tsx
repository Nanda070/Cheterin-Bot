import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { WelcomePage } from './Welcome'

describe('WelcomePage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the current toggle state', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: false })
    render(<WelcomePage />)

    const channelToggle = await screen.findByLabelText('Отправлять приветствие в канал')
    const dmToggle = screen.getByLabelText('Отправлять приветствие в личные сообщения')
    expect(channelToggle).toHaveAttribute('aria-checked', 'true')
    expect(dmToggle).toHaveAttribute('aria-checked', 'false')
  })

  it('toggles and saves the settings', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: true })
    const updateSpy = vi
      .spyOn(client, 'updateWelcomeSettings')
      .mockResolvedValue({ channel_enabled: false, dm_enabled: true })

    render(<WelcomePage />)
    fireEvent.click(await screen.findByLabelText('Отправлять приветствие в канал'))
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith({ channel_enabled: false, dm_enabled: true }),
    )
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('shows an error when saving fails', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: true })
    vi.spyOn(client, 'updateWelcomeSettings').mockRejectedValue(new Error('fail'))

    render(<WelcomePage />)
    fireEvent.click(await screen.findByText('Сохранить'))

    expect(await screen.findByText('Не удалось сохранить настройки')).toBeInTheDocument()
  })
})
