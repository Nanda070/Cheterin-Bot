import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Scroll window (and optional overflow mains) to top on every client-side route change. */
export function ScrollToTop() {
  const { pathname, search } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    document.documentElement.scrollTop = 0
    document.body.scrollTop = 0
    document.querySelectorAll<HTMLElement>('[data-scroll-reset]').forEach((el) => {
      el.scrollTop = 0
    })
  }, [pathname, search])

  return null
}
