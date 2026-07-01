import { loginUrl } from '../api/client'

export function LoginPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-6 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">Панель управления ботом</h1>
      <a
        href={loginUrl()}
        className="rounded-lg bg-indigo-600 px-6 py-3 font-medium transition hover:bg-indigo-500"
      >
        Войти через Discord
      </a>
    </div>
  )
}
