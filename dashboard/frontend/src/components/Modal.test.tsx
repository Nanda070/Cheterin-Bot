import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Modal } from './ui/Modal'

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(
      <Modal open={false} title="Заголовок" onClose={() => {}}>
        <p>Контент</p>
      </Modal>,
    )
    expect(screen.queryByText('Заголовок')).not.toBeInTheDocument()
  })

  it('renders title and children when open, closes on overlay click and Escape', () => {
    const onClose = vi.fn()
    render(
      <Modal open title="Подтверждение" onClose={onClose}>
        <p>Точно?</p>
      </Modal>,
    )
    expect(screen.getByText('Подтверждение')).toBeInTheDocument()
    expect(screen.getByText('Точно?')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('modal-overlay'))
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
