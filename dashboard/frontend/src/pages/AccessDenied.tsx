export function AccessDeniedPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">Доступ запрещён</h1>
      <p className="text-slate-400">У вас нет прав для просмотра этой панели.</p>
    </div>
  )
}
