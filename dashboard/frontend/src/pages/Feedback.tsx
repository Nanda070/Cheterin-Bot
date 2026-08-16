import { useState } from 'react'
import { useT } from '../context/LanguageContext'
import { FeedbackCasesPage } from './FeedbackCases'
import { FeedbackCategoriesPage } from './FeedbackCategories'
import { FeedbackPanelPage } from './FeedbackPanel'
import { IdeasPage } from './Ideas'

type Tab = 'cases' | 'categories' | 'panel' | 'ideas'

export function FeedbackPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('cases')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('cases')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'cases' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.cases')}
        </button>
        <button
          type="button"
          onClick={() => setTab('categories')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'categories' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.categories')}
        </button>
        <button
          type="button"
          onClick={() => setTab('panel')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'panel' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.panel')}
        </button>
        <button type="button" onClick={() => setTab('ideas')} className={`cursor-pointer px-3 py-2 text-sm font-medium ${tab === 'ideas' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'}`}>
          {t('ideas.title')}
        </button>
      </div>
      {tab === 'cases' ? <FeedbackCasesPage /> : tab === 'categories' ? <FeedbackCategoriesPage /> : tab === 'panel' ? <FeedbackPanelPage /> : <IdeasPage />}
    </div>
  )
}
