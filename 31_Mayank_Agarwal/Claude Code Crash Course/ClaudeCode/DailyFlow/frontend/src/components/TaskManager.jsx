import { useState } from 'react'
import TaskCard from './TaskCard'

const API = 'http://localhost:8000'

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * @param {{ tasks: object[], setTasks: (fn: (prev: object[]) => object[]) => void }} props
 */
export default function TaskManager({ tasks, setTasks }) {
  const [title, setTitle] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState(null)
  const [completingId, setCompletingId] = useState(null)
  const [showCompleted, setShowCompleted] = useState(false)

  const today = todayStr()
  const inProgress = tasks.filter(t => !t.completed)
  const completedToday = tasks.filter(
    t => t.completed && (t.completed_at || '').startsWith(today),
  )

  async function handleAdd(e) {
    e.preventDefault()
    if (!title.trim()) return
    setAdding(true)
    setAddError(null)
    try {
      const res = await fetch(`${API}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim() }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const detail = body.detail ?? 'Failed to add task'
        throw new Error(String(detail).split('\n')[0].slice(0, 120))
      }
      const task = await res.json()
      setTasks(prev => [task, ...prev])
      setTitle('')
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  async function handleComplete(id) {
    setCompletingId(id)
    try {
      const res = await fetch(`${API}/tasks/${id}/complete`, { method: 'PUT' })
      if (!res.ok) throw new Error('Failed to complete task')
      const updated = await res.json()
      setTasks(prev => prev.map(t => (t.id === id ? updated : t)))
    } finally {
      setCompletingId(null)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6">

      {/* Section header */}
      <div className="flex items-center gap-2 mb-5">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-sm">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M2 4h12M2 8h8M2 12h10" stroke="white" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </div>
        <h2 className="text-sm font-semibold text-slate-700">Smart Tasks</h2>
        {tasks.length > 0 && (
          <span className="ml-auto text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
            {completedToday.length}/{tasks.length} done
          </span>
        )}
      </div>

      {/* Add task form */}
      <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-2 mb-6">
        <input
          type="text"
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="What needs to get done today?"
          disabled={adding}
          className="flex-1 text-sm px-3.5 py-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={adding || !title.trim()}
          className="inline-flex items-center justify-center sm:justify-start gap-1.5 px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 active:scale-95 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer whitespace-nowrap flex-shrink-0"
        >
          {adding ? (
            <>
              <span className="spinner" />
              Adding…
            </>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              Add Task
            </>
          )}
        </button>
      </form>

      {addError && (
        <p className="text-red-500 text-xs mb-4 px-3 py-2 bg-red-50 rounded-lg border border-red-100">
          ⚠ {addError}
        </p>
      )}

      {/* In Progress */}
      {inProgress.length > 0 && (
        <div className="mb-5">
          <h3 className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest mb-3">
            In Progress · {inProgress.length}
          </h3>
          <div className="space-y-3">
            {inProgress.map((task, idx) => (
              <div key={task.id} style={{ animationDelay: `${idx * 0.05}s` }} className="task-stagger">
                <TaskCard
                  task={task}
                  onComplete={handleComplete}
                  isCompleting={completingId === task.id}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed Today */}
      {completedToday.length > 0 && (
        <div>
          <button
            onClick={() => setShowCompleted(v => !v)}
            className="flex items-center gap-2 w-full text-left mb-3 group"
          >
            <h3 className="text-[11px] font-semibold text-emerald-500 uppercase tracking-widest">
              Completed Today · {completedToday.length}
            </h3>
            <svg
              width="12" height="12" viewBox="0 0 12 12" fill="none"
              className={`ml-auto text-emerald-400 transition-transform duration-200 ${showCompleted ? 'rotate-180' : ''}`}
            >
              <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          {showCompleted && (
            <div className="space-y-3">
              {completedToday.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={handleComplete}
                  isCompleting={false}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {tasks.length === 0 && (
        <div className="text-center py-12">
          <div className="flex justify-center mb-4">
            <div className="text-5xl animate-bounce" style={{ animationDuration: '2s' }}>📝</div>
          </div>
          <p className="text-sm font-semibold text-slate-700 mb-1">Add your first task to get started</p>
          <p className="text-xs text-slate-500 mb-4">Write a task title above and AI will break it down into actionable steps</p>
          <div className="inline-flex items-center gap-2 text-xs text-slate-400 bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
              <path d="M8 1v6M1 8h6M13 8h2M8 13v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Tip: Try "Build a landing page" or "Learn React"
          </div>
        </div>
      )}
    </div>
  )
}
