import { useState, useEffect } from 'react'
import Confetti from './Confetti'

/**
 * @param {{
 *   task: object,
 *   onComplete: (id: string) => Promise<void>,
 *   isCompleting: boolean,
 * }} props
 */
export default function TaskCard({ task, onComplete, isCompleting }) {
  const [checked, setChecked] = useState(new Set())
  const [showConfetti, setShowConfetti] = useState(false)
  const prevCompletedRef = useState(task.completed)[0]

  const toggle = idx => {
    setChecked(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  const handleComplete = async () => {
    console.log('Marking task complete:', task.id)
    await onComplete(task.id)
  }

  // Trigger confetti when task completes
  useEffect(() => {
    if (task.completed && !isCompleting && !prevCompletedRef) {
      console.log('Task just completed! Showing confetti')
      setShowConfetti(true)
      const timer = setTimeout(() => setShowConfetti(false), 100)
      return () => clearTimeout(timer)
    }
  }, [task.completed, isCompleting])

  const isCompleted = task.completed

  return (
    <>
      <Confetti trigger={showConfetti} />
      
      <div
        className={`task-enter relative rounded-xl border p-4 shadow-sm transition-all duration-300 overflow-hidden ${
          isCompleted
            ? 'bg-emerald-50 border-emerald-200'
            : 'bg-white border-slate-200'
        }`}
      >
        {/* Left accent stripe */}
        <span
          aria-hidden="true"
          className={`absolute left-0 inset-y-0 w-[3px] ${isCompleted ? 'bg-emerald-400' : 'bg-indigo-500'}`}
        />
        {/* Title row */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5 min-w-0">
            {isCompleted ? (
              <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 animate-bounce" style={{ animationDuration: '0.6s' }}>
                <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            ) : (
              <div className="mt-0.5 w-5 h-5 rounded-full border-2 border-slate-300 flex-shrink-0" />
            )}
            <span
              className={`text-sm font-semibold leading-snug ${
                isCompleted ? 'text-slate-400' : 'text-slate-800'
              }`}
            >
              {isCompleted ? <span className="strike">{task.title}</span> : task.title}
            </span>
          </div>

          {isCompleted && (
            <span className="flex-shrink-0 text-[10px] font-semibold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200 animate-bounce" style={{ animationDuration: '0.6s' }}>
              Done
            </span>
          )}
        </div>

        {/* Subtasks */}
        {task.subtasks?.length > 0 && (
          <ul className="mt-3 space-y-1.5 ml-7">
            {task.subtasks.map((sub, idx) => (
              <li key={idx} className="flex items-start gap-2 group">
                <button
                  onClick={() => !isCompleted && toggle(idx)}
                  className={`mt-0.5 w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center transition-colors ${
                    isCompleted || checked.has(idx)
                      ? 'bg-indigo-500 border-indigo-500'
                      : 'border-slate-300 group-hover:border-indigo-300 cursor-pointer'
                  }`}
                  aria-label={`Toggle subtask: ${sub}`}
                >
                  {(isCompleted || checked.has(idx)) && (
                    <svg width="8" height="8" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </button>
                <span
                  className={`text-xs leading-relaxed transition-colors ${
                    isCompleted || checked.has(idx)
                      ? 'line-through text-slate-400'
                      : 'text-slate-600'
                  }`}
                >
                  {sub}
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* Complete button */}
        {!isCompleted && (
          <div className="mt-4 ml-7">
            <button
              onClick={handleComplete}
              disabled={isCompleting}
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95 transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            >
              {isCompleting ? (
                <>
                  <span className="spinner" />
                  Completing…
                </>
              ) : (
                <>
                  <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Mark Complete
                </>
              )}
            </button>
          </div>
        )}

        {/* Completed timestamp */}
        {isCompleted && task.completed_at && (
          <p className="mt-2 ml-7 text-[11px] text-slate-400">
            Completed at {new Date(task.completed_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </>
  )
}
