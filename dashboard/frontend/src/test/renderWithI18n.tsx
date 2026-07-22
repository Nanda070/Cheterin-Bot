import type { ReactElement } from 'react'
import { render } from '@testing-library/react'
import { LanguageProvider } from '../context/LanguageContext'

/** Render with LanguageProvider (Russian default). */
export function renderWithI18n(ui: ReactElement) {
  return render(<LanguageProvider>{ui}</LanguageProvider>)
}
