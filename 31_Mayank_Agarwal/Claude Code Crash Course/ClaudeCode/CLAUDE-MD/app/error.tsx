'use client'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex h-screen flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
      <h1 className="text-2xl font-bold text-red-600 dark:text-red-500">Error</h1>
      <p className="mt-2 text-gray-600 dark:text-slate-400">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 rounded-lg bg-blue-600 dark:bg-blue-500 px-4 py-2 text-white hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors"
      >
        Try again
      </button>
    </div>
  )
}
