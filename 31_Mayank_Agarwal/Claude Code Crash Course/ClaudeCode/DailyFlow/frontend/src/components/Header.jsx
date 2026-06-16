import WeatherWidget from './WeatherWidget'

/**
 * @param {{ onRefreshBriefing: () => void }} props
 */
export default function Header({ onRefreshBriefing }) {
  const now = new Date()
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <header
      className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 fade-slide-up"
      style={{ animationDelay: '0s' }}
    >
      <div className="flex-1">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent tracking-tight">
          DailyPulse
        </h1>
        <p className="text-slate-400 text-sm mt-0.5 font-medium">{dateStr}</p>
      </div>

      {/* Weather Widget in top right */}
      <div className="flex-shrink-0">
        <WeatherWidget />
      </div>

      <button
        onClick={onRefreshBriefing}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium rounded-lg shadow-sm hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-600 transition-all duration-200 cursor-pointer self-start sm:self-auto"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
          <path d="M8 16H3v5"/>
        </svg>
        Refresh Briefing
      </button>
    </header>
  )
}
