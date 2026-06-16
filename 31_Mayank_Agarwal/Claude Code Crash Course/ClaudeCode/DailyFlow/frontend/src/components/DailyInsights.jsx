import { useState } from 'react'

const API = 'http://localhost:8000'

/** Renders **bold** markdown tokens as <strong>. */
function FormattedText({ text }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i} className="font-semibold text-slate-800">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </p>
  )
}

/**
 * @param {{ tasks: object[] }} props
 */
export default function DailyInsights({ tasks }) {
  const [insights, setInsights] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  if (tasks.length < 3) {
    return (
      <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-5 flex flex-col items-center justify-center text-center gap-2 min-h-[120px]">
        <div className="text-2xl">🔒</div>
        <p className="text-xs font-medium text-slate-500">Daily Insights</p>
        <p className="text-xs text-slate-400">
          Add {3 - tasks.length} more task{3 - tasks.length !== 1 ? 's' : ''} to unlock
        </p>
        <div className="flex gap-1 mt-1">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full ${i < tasks.length ? 'bg-indigo-500' : 'bg-slate-200'}`}
            />
          ))}
        </div>
      </div>
    )
  }

  async function handleInsights() {
    setLoading(true)
    setError(null)
    setInsights('')
    try {
      const res = await fetch(`${API}/insights`)
      if (!res.ok) throw new Error('Failed to get insights')
      const data = await res.json()
      setInsights(data.insights)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col flex-1">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-sm">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.1 3.1l1.4 1.4M11.5 11.5l1.4 1.4M3.1 12.9l1.4-1.4M11.5 4.5l1.4-1.4" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="8" r="2.5" fill="white" />
          </svg>
        </div>
        <h2 className="text-sm font-semibold text-slate-700">Daily Insights</h2>
      </div>

      <button
        onClick={handleInsights}
        disabled={loading}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-medium rounded-lg hover:from-amber-600 hover:to-orange-600 active:scale-[0.98] transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer shadow-sm"
      >
        {loading ? (
          <>
            <span className="spinner" />
            Analysing…
          </>
        ) : (
          <>
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8 5v3.5l2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Get Insights
          </>
        )}
      </button>

      {error && (
        <p className="mt-3 text-red-500 text-xs px-3 py-2 bg-red-50 rounded-lg border border-red-100">
          ⚠ {error}
        </p>
      )}

      {insights && !loading && (
        <div className="mt-4 fade-in bg-amber-50 rounded-xl border border-amber-100 p-4">
          <FormattedText text={insights} />
        </div>
      )}
    </div>
  )
}
