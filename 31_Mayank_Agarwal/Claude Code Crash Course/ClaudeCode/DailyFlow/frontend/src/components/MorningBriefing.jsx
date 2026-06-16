import { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

function SkeletonBlock({ className = '' }) {
  return <span className={`shimmer ${className}`} style={{ borderRadius: 6 }} />
}

function BriefingSkeleton() {
  return (
    <div className="grid sm:grid-cols-3 gap-4 mt-2">
      {[0, 1, 2].map(i => (
        <div key={i} className="bg-white/60 rounded-xl p-4 border border-white space-y-2">
          <SkeletonBlock className="h-3 w-16" />
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="h-4 w-5/6" />
        </div>
      ))}
    </div>
  )
}

function NewsItemSkeleton() {
  return (
    <div className="space-y-2">
      <SkeletonBlock className="h-3 w-full" />
      <SkeletonBlock className="h-3 w-5/6" />
    </div>
  )
}

/**
 * @param {{ icon: string, label: string, text: string }} props
 */
function BriefingItem({ icon, label, text }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-xl p-4 border border-white/80 shadow-sm fade-in">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-sm">{icon}</span>
        <span className="text-[10px] font-semibold text-indigo-600 uppercase tracking-widest">
          {label}
        </span>
      </div>
      <p className="text-slate-700 text-sm leading-relaxed">{text}</p>
    </div>
  )
}

/**
 * @param {{ title: string, content: string }} props
 */
function NewsItem({ title, content }) {
  return (
    <div className="bg-white/50 backdrop-blur-sm rounded-lg p-3 border border-white/60 hover:bg-white/70 transition-colors">
      <p className="text-xs font-semibold text-indigo-700 mb-1 leading-snug">{title}</p>
      <p className="text-xs text-slate-600 leading-relaxed">{content}</p>
    </div>
  )
}

export default function MorningBriefing() {
  const [briefing, setBriefing] = useState(null)
  const [aiNews, setAiNews] = useState([])
  const [loading, setLoading] = useState(true)
  const [newsLoading, setNewsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchBriefing = () => {
    setLoading(true)
    setError(null)
    fetch(`${API}/briefing`)
      .then(r => {
        if (!r.ok) throw new Error('Could not load briefing')
        return r.json()
      })
      .then(data => { setBriefing(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }

  const fetchAiNews = () => {
    setNewsLoading(true)
    fetch(`${API}/ai-news`)
      .then(r => {
        if (!r.ok) throw new Error('Could not load AI news')
        return r.json()
      })
      .then(data => { setAiNews(data.news || []); setNewsLoading(false) })
      .catch(() => { setAiNews([]); setNewsLoading(false) })
  }

  const handleRefresh = () => {
    fetchBriefing()
    fetchAiNews()
  }

  useEffect(() => {
    fetchBriefing()
    fetchAiNews()
  }, [])

  return (
    <div className="space-y-4">
      {/* Main Briefing Card */}
      <div className="gradient-border rounded-2xl shadow-md">
        <div className="bg-gradient-to-br from-indigo-50 via-white to-violet-50 rounded-2xl p-5 sm:p-6">
          {/* Card header */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-xs shadow-sm">
                🌅
              </div>
              <h2 className="text-sm font-semibold text-slate-700">Morning Briefing</h2>
              {!loading && briefing && (
                <span className="text-[11px] text-slate-400 bg-white px-2.5 py-0.5 rounded-full border border-slate-100 font-medium">
                  {briefing.date}
                </span>
              )}
            </div>
            <button
              onClick={handleRefresh}
              disabled={loading || newsLoading}
              className="px-3 py-1.5 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:bg-slate-300 text-white text-xs font-medium transition-colors"
              title="Refresh briefing and news"
            >
              {loading || newsLoading ? '⟳ Loading...' : '⟳ Refresh'}
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-500 text-sm py-4 px-3 bg-red-50 rounded-xl border border-red-100 mb-4">
              <span>⚠</span>
              <span>{error}</span>
            </div>
          )}

          {loading && <BriefingSkeleton />}

          {!loading && !error && briefing && (
            <div className="space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <BriefingItem icon="💬" label="Quote" text={briefing.quote} />
                <BriefingItem icon="🎯" label="Focus Tip" text={briefing.focus_tip} />
                <BriefingItem icon="✨" label="Today's Message" text={briefing.message} />
              </div>

              {/* Web Tip Section */}
              {briefing.web_tip && (
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">💡</span>
                    <span className="text-[10px] font-semibold text-amber-700 uppercase tracking-widest">
                      Web Insight
                    </span>
                  </div>
                  <p className="text-slate-700 text-sm leading-relaxed">{briefing.web_tip}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* AI News Card */}
      <div className="gradient-border rounded-2xl shadow-md">
        <div className="bg-gradient-to-br from-slate-50 via-white to-blue-50 rounded-2xl p-5 sm:p-6">
          {/* Card header */}
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-xs shadow-sm">
              🤖
            </div>
            <h2 className="text-sm font-semibold text-slate-700">Latest AI News</h2>
          </div>

          {newsLoading && (
            <div className="space-y-3">
              {[0, 1, 2].map(i => (
                <NewsItemSkeleton key={i} />
              ))}
            </div>
          )}

          {!newsLoading && aiNews.length > 0 && (
            <div className="grid gap-3">
              {aiNews.map((item, i) => (
                <NewsItem key={i} title={item.title} content={item.content} />
              ))}
            </div>
          )}

          {!newsLoading && aiNews.length === 0 && (
            <div className="text-slate-500 text-sm py-4 text-center">
              No AI news available
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
