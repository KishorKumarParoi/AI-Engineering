import React from 'react'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export function Textarea({ label, error, className, ...props }: TextareaProps) {
  return (
    <div className="flex flex-col">
      {label && (
        <label className="mb-1 text-sm font-medium text-gray-700 dark:text-slate-300">
          {label}
        </label>
      )}
      <textarea
        className={`rounded-md border bg-white dark:bg-slate-800 px-3 py-2 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors ${
          error
            ? 'border-red-500 dark:border-red-600'
            : 'border-gray-300 dark:border-slate-600'
        } placeholder:text-gray-400 dark:placeholder:text-slate-500 ${className || ''}`}
        {...props}
      />
      {error && (
        <span className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</span>
      )}
    </div>
  )
}
