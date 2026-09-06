import { ArrowLeft, ArrowRight, Check, Copy } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PublicLayout } from '../components/PublicLayout'
import { DocsBanner } from '../components/docs/DocsBanner'
import type { DocNavItem } from '../components/docs/docsNav'
import { DocsSearch } from '../components/docs/DocsSearch'
import { DocsSidebar } from '../components/docs/DocsSidebar'
import { DocsToc } from '../components/docs/DocsToc'
import { useLanguage } from '../context/LanguageContext'
import { getDocGroups, getDocSections } from './docs/index'

export function DocsPage() {
  const { sectionId } = useParams()
  const { lang, t } = useLanguage()
  const sections = getDocSections(lang)
  const groups = [...getDocGroups(lang)]
  const navItems: DocNavItem[] = sections.map((s) => ({ id: s.id, title: s.title, group: s.group }))

  const active = sections.find((s) => s.id === sectionId) ?? sections[0]
  const activeIndex = sections.indexOf(active)
  const prevSection = activeIndex > 0 ? sections[activeIndex - 1] : null
  const nextSection = activeIndex < sections.length - 1 ? sections[activeIndex + 1] : null

  const articleRef = useRef<HTMLElement>(null)
  const [copied, setCopied] = useState(false)
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current)
    }
  }, [])

  const copyPage = async () => {
    const text = articleRef.current?.innerText ?? ''
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current)
      copyTimeoutRef.current = setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard API unavailable (permissions/http context) — non-critical affordance, ignore.
    }
  }

  return (
    <PublicLayout>
      <div className="docs-shell">
      <DocsBanner />
      <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
        <aside className="shrink-0 lg:w-56 xl:w-60">
          <DocsSearch items={navItems} />
          <DocsSidebar items={navItems} groups={groups} activeId={active.id} />
        </aside>

        <article
          key={`${lang}-${active.id}`}
          ref={articleRef}
          className="animate-fade-in-up min-w-0 flex-1 rounded-card border border-border bg-surface p-6 lg:max-w-none xl:pr-2"
        >
          <div className="mb-2 flex items-start justify-between gap-3">
            <h1 className="border-l-2 border-primary pl-3 text-lg font-semibold text-foreground">{active.title}</h1>
            <button
              type="button"
              onClick={copyPage}
              className="flex shrink-0 cursor-pointer items-center gap-1.5 rounded-control border border-border px-2.5 py-1.5 text-xs text-muted transition-colors hover:border-primary hover:text-foreground"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              {copied ? t('docsShell.copied') : t('docsShell.copyPage')}
            </button>
          </div>
          {active.content}

          {(prevSection || nextSection) && (
            <div
              role="navigation"
              aria-label={t('docsShell.pager')}
              className="mt-8 flex items-center justify-between gap-3 border-t border-border pt-4"
            >
              {prevSection ? (
                <Link
                  to={`/docs/${prevSection.id}`}
                  className="flex items-center gap-1.5 rounded-control px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
                >
                  <ArrowLeft size={14} />
                  {prevSection.title}
                </Link>
              ) : (
                <span />
              )}
              {nextSection && (
                <Link
                  to={`/docs/${nextSection.id}`}
                  className="flex items-center gap-1.5 rounded-control px-3 py-2 text-right text-sm text-muted transition-colors hover:text-foreground"
                >
                  {nextSection.title}
                  <ArrowRight size={14} />
                </Link>
              )}
            </div>
          )}
        </article>

        <DocsToc containerRef={articleRef} activeId={active.id} />
      </div>
      </div>
    </PublicLayout>
  )
}
