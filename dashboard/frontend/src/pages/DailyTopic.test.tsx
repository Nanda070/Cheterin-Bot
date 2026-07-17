import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { DailyTopicPage } from './DailyTopic'

const emptySettings: client.DailyTopicSettings = { enabled: false, channel_id: '', post_times: [], topics: [] }

function mockBaseFetches(settings: client.DailyTopicSettings = emptySettings) {
  vi.spyOn(client, 'fetchDailyTopic').mockResolvedValue(settings)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
}

describe('DailyTopicPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders defaults with no topics and no post times', async () => {
    mockBaseFetches()
    render(<DailyTopicPage />)

    expect(await screen.findByText('Ежедневная рубрика')).toBeInTheDocument()
    expect(screen.getByText('Время не задано')).toBeInTheDocument()
    expect(screen.getByText('Тем пока нет — добавьте хотя бы одну, чтобы включить рубрику.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Опубликовать сейчас' })).toBeDisabled()
  })

  it('toggles enabled and saves settings', async () => {
    mockBaseFetches({ enabled: false, channel_id: '500', post_times: ['09:00'], topics: [] })
    const saveSpy = vi.spyOn(client, 'updateDailyTopicSettings').mockResolvedValue({
      enabled: true,
      channel_id: '500',
      post_times: ['09:00'],
      topics: [],
    })

    render(<DailyTopicPage />)
    await screen.findByText('Ежедневная рубрика')

    fireEvent.click(screen.getByRole('switch'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(saveSpy).toHaveBeenCalledWith({ enabled: true, channel_id: '500', post_times: ['09:00'] }),
    )
  })

  it('adds and removes a post time before saving', async () => {
    mockBaseFetches()
    const saveSpy = vi.spyOn(client, 'updateDailyTopicSettings').mockResolvedValue(emptySettings)

    render(<DailyTopicPage />)
    await screen.findByText('Ежедневная рубрика')

    const timeInput = document.querySelector('input[type="time"]') as HTMLInputElement
    fireEvent.change(timeInput, { target: { value: '09:00' } })
    fireEvent.click(screen.getByRole('button', { name: /Добавить время/ }))

    expect(screen.getByText('09:00')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))
    await waitFor(() =>
      expect(saveSpy).toHaveBeenCalledWith({ enabled: false, channel_id: '', post_times: ['09:00'] }),
    )
  })

  it('adds a new topic via the modal', async () => {
    mockBaseFetches()
    const createSpy = vi.spyOn(client, 'createDailyTopic').mockResolvedValue({ id: '1', text: 'Вопрос дня?' })

    render(<DailyTopicPage />)
    await screen.findByText('Ежедневная рубрика')

    fireEvent.click(screen.getByRole('button', { name: /Добавить тему/ }))
    fireEvent.change(screen.getByLabelText('Текст темы/вопроса'), { target: { value: 'Вопрос дня?' } })
    fireEvent.click(screen.getByRole('button', { name: 'Добавить' }))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('Вопрос дня?'))
  })

  it('edits an existing topic', async () => {
    mockBaseFetches({ enabled: false, channel_id: '', post_times: [], topics: [{ id: '1', text: 'Старый вопрос' }] })
    const updateSpy = vi.spyOn(client, 'updateDailyTopic').mockResolvedValue({ id: '1', text: 'Новый вопрос' })

    render(<DailyTopicPage />)
    expect(await screen.findByText('Старый вопрос')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Изменить' }))
    const textarea = screen.getByDisplayValue('Старый вопрос')
    fireEvent.change(textarea, { target: { value: 'Новый вопрос' } })
    const saveButtons = screen.getAllByRole('button', { name: 'Сохранить' })
    fireEvent.click(saveButtons[saveButtons.length - 1])

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith('1', 'Новый вопрос'))
  })

  it('deletes a topic', async () => {
    mockBaseFetches({ enabled: false, channel_id: '', post_times: [], topics: [{ id: '1', text: 'Вопрос' }] })
    const deleteSpy = vi.spyOn(client, 'deleteDailyTopic').mockResolvedValue()

    render(<DailyTopicPage />)
    expect(await screen.findByText('Вопрос')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Удалить тему' }))
    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('1'))
  })

  it('posts the topic now and shows a confirmation', async () => {
    mockBaseFetches({ enabled: false, channel_id: '500', post_times: [], topics: [{ id: '1', text: 'Вопрос' }] })
    const postSpy = vi.spyOn(client, 'postDailyTopicNow').mockResolvedValue({ ok: true, topic: { id: '1', text: 'Вопрос' } })

    render(<DailyTopicPage />)
    const postButton = await screen.findByRole('button', { name: 'Опубликовать сейчас' })
    expect(postButton).not.toBeDisabled()

    fireEvent.click(postButton)

    await waitFor(() => expect(postSpy).toHaveBeenCalled())
    expect(await screen.findByText('Тема дня опубликована.')).toBeInTheDocument()
  })
})
