import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { NotFoundPage } from './NotFound'

describe('NotFoundPage', () => {
  it('renders a message and a link back home', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('Страница не найдена')).toBeInTheDocument()
    const link = screen.getByText('Вернуться на главную')
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })
})
