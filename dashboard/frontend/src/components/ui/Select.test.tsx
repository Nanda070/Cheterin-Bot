import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Select } from './Select'
import { renderWithLanguage } from '../../test/renderWithLanguage'

describe('Select channel dead badge', () => {
  it('shows dead badge and disables unusable channels for new picks', () => {
    const onChange = vi.fn()
    renderWithLanguage(
      <Select
        value=""
        onChange={onChange}
        options={[
          { id: '1', name: 'alive', bot_can_view: true, bot_can_send: true },
          { id: '2', name: 'locked', bot_can_view: true, bot_can_send: false },
        ]}
        placeholder="Pick"
        ariaLabel="channel"
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'channel' }))

    expect(screen.getByRole('option', { name: /locked/i })).toBeDisabled()
    expect(screen.getAllByText('мёртв').length).toBeGreaterThanOrEqual(1)

    fireEvent.click(screen.getByRole('option', { name: /alive/i }))
    expect(onChange).toHaveBeenCalledWith('1')
  })

  it('keeps currently selected dead channel visible with badge', () => {
    const onChange = vi.fn()
    renderWithLanguage(
      <Select
        value="2"
        onChange={onChange}
        options={[
          { id: '1', name: 'alive', bot_can_view: true, bot_can_send: true },
          { id: '2', name: 'locked', bot_can_view: true, bot_can_send: false },
        ]}
        ariaLabel="channel"
      />,
    )

    expect(screen.getByText('locked')).toBeInTheDocument()
    expect(screen.getByText('мёртв')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'channel' }))
    const lockedOption = screen.getByRole('option', { name: /locked/i })
    expect(lockedOption).not.toBeDisabled()
    fireEvent.click(lockedOption)
    expect(onChange).toHaveBeenCalledWith('2')
  })

  it('allowClear offers a none option that clears the value', () => {
    const onChange = vi.fn()
    renderWithLanguage(
      <Select
        value="1"
        onChange={onChange}
        options={[{ id: '1', name: 'alive', bot_can_view: true, bot_can_send: true }]}
        ariaLabel="channel"
        allowClear
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'channel' }))
    fireEvent.click(screen.getByRole('option', { name: '—' }))
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('synthesizes a placeholder + deleted badge for a saved value missing from options', () => {
    const onChange = vi.fn()
    renderWithLanguage(
      <Select
        value="999"
        onChange={onChange}
        options={[{ id: '1', name: 'alive', bot_can_view: true, bot_can_send: true }]}
        ariaLabel="channel"
      />,
    )

    expect(screen.getByText('#999')).toBeInTheDocument()
    expect(screen.getByText('удалён')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'channel' }))
    const deletedOption = screen.getByRole('option', { name: /#999/i })
    expect(deletedOption).not.toBeDisabled()
  })
})
