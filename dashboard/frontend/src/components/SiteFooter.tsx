import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { fetchInviteUrl } from '../api/client'
import { useT } from '../context/LanguageContext'

const SOCIAL = {
  github: 'https://github.com/nanda070/',
  discord: 'https://discord.gg/cheterin',
  mail: 'mailto:adnan.huseynli1@gmail.com',
} as const

/** Exact EN bottom-bar copy from product request. */
const BOTTOM_DISCLAIMER =
  'Disclaimer: Discord Cheterin Bot and Lookup is an independent tool and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Discord Inc. or any of its subsidiaries or affiliates. Discord and its logos are trademarks of Discord Inc.'

const BOTTOM_COPYRIGHT = '© 2026 Cheterin Group. All rights reserved.'

function SocialBtn({ href, label, children }: { href: string; label: string; children: ReactNode }) {
  const external = !href.startsWith('mailto:')
  return (
    <a
      href={href}
      target={external ? '_blank' : undefined}
      rel={external ? 'noreferrer' : undefined}
      aria-label={label}
      className="inline-flex h-9 w-9 items-center justify-center rounded-[8px] border border-border/80 bg-surface text-muted transition-colors hover:border-primary/40 hover:bg-surface-hover hover:text-foreground"
    >
      {children}
    </a>
  )
}

function ColHeading({ children }: { children: ReactNode }) {
  return <h2 className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-foreground">{children}</h2>
}

function ColLink({ href, to, children }: { href?: string; to?: string; children: ReactNode }) {
  const className = 'text-sm text-muted transition-colors hover:text-foreground'
  if (to) {
    return (
      <Link to={to} className={className}>
        {children}
      </Link>
    )
  }
  return (
    <a href={href} className={className} target={href?.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
      {children}
    </a>
  )
}

function GithubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
    </svg>
  )
}

function DiscordIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03ZM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418Zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418Z" />
    </svg>
  )
}

function MailIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </svg>
  )
}

type Props = { descriptionSlot?: ReactNode }

export function SiteFooter({ descriptionSlot }: Props) {
  const t = useT()
  const [inviteBusy, setInviteBusy] = useState(false)

  const openInvite = async () => {
    setInviteBusy(true)
    try {
      const url = await fetchInviteUrl()
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch {
      window.open(SOCIAL.discord, '_blank', 'noopener,noreferrer')
    } finally {
      setInviteBusy(false)
    }
  }

  return (
    <footer className="site-footer mt-auto border-t border-border">
      <div className="site-footer-grid mx-auto w-full max-w-6xl px-4 py-12 sm:px-6">
        <div className="min-w-0">
          <p className="font-semibold tracking-tight text-foreground">Cheterin Group</p>
          {descriptionSlot ?? (
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-muted">{t('siteFooter.bot.desc')}</p>
          )}
          <div className="mt-5 flex items-center gap-2">
            <SocialBtn href={SOCIAL.github} label="GitHub">
              <GithubIcon />
            </SocialBtn>
            <SocialBtn href={SOCIAL.discord} label="Discord">
              <DiscordIcon />
            </SocialBtn>
            <SocialBtn href={SOCIAL.mail} label="Email">
              <MailIcon />
            </SocialBtn>
          </div>
        </div>

        <div>
          <ColHeading>{t('siteFooter.col.services')}</ColHeading>
          <ul className="mt-4 flex flex-col gap-2.5">
            <li>
              <ColLink to="/about">{t('siteFooter.bot.modules')}</ColLink>
            </li>
            <li>
              <ColLink to="/docs">{t('siteFooter.bot.docs')}</ColLink>
            </li>
            <li>
              <ColLink href="/lookup/">{t('siteFooter.bot.lookup')}</ColLink>
            </li>
            <li>
              <ColLink to="/servers">{t('siteFooter.bot.dashboard')}</ColLink>
            </li>
          </ul>
        </div>

        <div>
          <ColHeading>{t('siteFooter.col.legal')}</ColHeading>
          <ul className="mt-4 flex flex-col gap-2.5">
            <li>
              <ColLink to="/terms">{t('siteFooter.legal.terms')}</ColLink>
            </li>
            <li>
              <ColLink to="/privacy">{t('siteFooter.legal.privacy')}</ColLink>
            </li>
            <li>
              <ColLink to="/cookies">{t('siteFooter.legal.cookies')}</ColLink>
            </li>
            <li>
              <ColLink to="/disclaimer">{t('siteFooter.legal.disclaimer')}</ColLink>
            </li>
          </ul>
        </div>

        <div>
          <ColHeading>{t('siteFooter.col.community')}</ColHeading>
          <ul className="mt-4 flex flex-col gap-2.5">
            <li>
              <ColLink href={SOCIAL.discord}>{t('siteFooter.bot.support')}</ColLink>
            </li>
            <li>
              <button
                type="button"
                disabled={inviteBusy}
                onClick={() => void openInvite()}
                className="cursor-pointer text-left text-sm text-muted transition-colors hover:text-foreground disabled:opacity-60"
              >
                {t('siteFooter.bot.add')}
              </button>
            </li>
            <li>
              <ColLink to="/credits">{t('siteFooter.bot.credits')}</ColLink>
            </li>
            <li>
              <ColLink to="/dev-blog">{t('siteFooter.bot.devBlog')}</ColLink>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border/70">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-4 py-5 sm:flex-row sm:items-start sm:justify-between sm:gap-8 sm:px-6">
          <p className="max-w-3xl text-[0.7rem] leading-relaxed text-muted/80">{BOTTOM_DISCLAIMER}</p>
          <p className="shrink-0 text-[0.7rem] text-muted/80 sm:text-right">{BOTTOM_COPYRIGHT}</p>
        </div>
      </div>
    </footer>
  )
}
