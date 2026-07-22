import { Info, Warning } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { useLanguage } from '../../context/LanguageContext'

export interface DocSection {
  id: string
  title: string
  group: string
  content: ReactNode
}

export function HeadingAnchor() {
  const { t } = useLanguage()
  return (
    <button
      type="button"
      aria-label={t('docsShell.copySectionLink')}
      onClick={(event) => {
        const id = event.currentTarget.parentElement?.id
        if (!id) return
        history.replaceState(null, '', `#${id}`)
        event.currentTarget.parentElement?.scrollIntoView({ block: 'start', behavior: 'smooth' })
      }}
      className="ml-2 cursor-pointer text-muted opacity-0 transition-opacity group-hover:opacity-60 hover:!opacity-100"
    >
      #
    </button>
  )
}

export function H(props: { children: ReactNode }) {
  return (
    <h2 className="group mt-6 flex items-center text-base font-semibold text-foreground first:mt-0">
      {props.children}
      <HeadingAnchor />
    </h2>
  )
}

export function H3(props: { children: ReactNode }) {
  return (
    <h3 className="group mt-4 flex items-center text-sm font-semibold text-foreground">
      {props.children}
      <HeadingAnchor />
    </h3>
  )
}

export function P(props: { children: ReactNode }) {
  return <p className="mt-2 text-sm leading-relaxed text-muted">{props.children}</p>
}

export function UL(props: { children: ReactNode }) {
  return <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-sm leading-relaxed text-muted">{props.children}</ul>
}

export function OL(props: { children: ReactNode }) {
  return <ol className="mt-2 flex list-decimal flex-col gap-1 pl-5 text-sm leading-relaxed text-muted">{props.children}</ol>
}

export function Code(props: { children: ReactNode }) {
  return <code className="rounded bg-surface-hover px-1.5 py-0.5 text-xs text-foreground">{props.children}</code>
}

export function Note(props: { children: ReactNode }) {
  return (
    <div className="mt-3 flex gap-2.5 rounded-control border border-primary/40 bg-primary-muted p-3 text-sm leading-relaxed text-foreground">
      <Info size={18} weight="fill" className="mt-0.5 shrink-0 text-primary" />
      <div className="min-w-0">{props.children}</div>
    </div>
  )
}

export function Warn(props: { children: ReactNode }) {
  return (
    <div className="mt-3 flex gap-2.5 rounded-control border border-warning/40 bg-warning/10 p-3 text-sm leading-relaxed text-foreground">
      <Warning size={18} weight="fill" className="mt-0.5 shrink-0 text-warning" />
      <div className="min-w-0">{props.children}</div>
    </div>
  )
}

export function Table(props: { headers: string[]; rows: ReactNode[][] }) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full min-w-120 border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted">
            {props.headers.map((h) => (
              <th key={h} className="py-2 pr-4 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.rows.map((row, i) => (
            <tr key={i} className="border-b border-border last:border-b-0 align-top">
              {row.map((cell, j) => (
                <td key={j} className={`py-2 pr-4 ${j === 0 ? 'whitespace-nowrap text-foreground' : 'text-muted'}`}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
