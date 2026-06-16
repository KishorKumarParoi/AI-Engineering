import { useState } from 'react'

const API = 'http://localhost:8000'

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Renders **bold** markdown tokens as <strong>. */
function FormattedStandup({ text }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <p className="font-mono text-[12.5px] text-slate-300 leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i} className="font-bold text-white">
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
export default function StandupGenerator({ tasks }) {
  const [standup, setStandup] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const today = todayStr()
  const completedToday = tasks.filter(
    t => t.completed && (t.completed_at || '').startsWith(today),
  )

  if (completedToday.length === 0) return null

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    setStandup('')
    try {
      const res = await fetch(`${API}/standup`)
      if (!res.ok) throw new Error('Failed to generate standup')
      const data = await res.json()
      setStandup(data.standup)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(standup)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col flex-1">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center shadow-sm">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M3 4h10M3 8h7M3 12h5" stroke="white" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </div>
        <h2 className="text-sm font-semibold text-slate-700">Standup Generator</h2>
        <span className="ml-auto text-[11px] font-medium text-violet-600 bg-violet-50 px-2 py-0.5 rounded-full border border-violet-100">
          {completedToday.length} task{completedToday.length !== 1 ? 's' : ''} done
        </span>
      </div>

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-medium rounded-lg hover:from-indigo-700 hover:to-violet-700 active:scale-[0.98] transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer shadow-sm"
      >
        {loading ? (
          <>
            <span className="spinner" />
            Generating…
          </>
        ) : (
          <>
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <path d="M8 1l2 5h5l-4 3 1.5 5L8 11l-4.5 3L5 9 1 6h5z" fill="currentColor" />
            </svg>
            Generate Standup
          </>
        )}
      </button>

      {error && (
        <p className="mt-3 text-red-500 text-xs px-3 py-2 bg-red-50 rounded-lg border border-red-100">
          ⚠ {error}
        </p>
      )}

      {standup && !loading && (
        <div className="mt-4 fade-in">
          <div className="bg-slate-900 rounded-xl border border-slate-700 p-4">
            <div className="flex items-center gap-1.5 mb-3">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
            </div>
            <FormattedStandup text={standup} />
          </div>
          <div className="relative mt-3">
            <button
              onClick={handleCopy}
              className={`w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border transition-all duration-200 cursor-pointer ${
                copied
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
              }`}
            >
              {copied ? (
                <>
                  <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
                    <rect x="5" y="5" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M9 5V3a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                  Copy to Clipboard
                </>
              )}
            </button>
            {copied && (
              <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-lg">
                <div className="absolute inset-0 bg-emerald-400/10 fade-out-delayed" />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
