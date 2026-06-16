interface EmptyStateProps {
  title: string
  description?: string
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 dark:border-slate-700 px-6 py-8 text-center">
      <div className="mb-3 text-4xl opacity-40">📭</div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
        {title}
      </h3>
      {description && (
        <p className="mt-2 text-sm text-gray-600 dark:text-slate-400">
          {description}
        </p>
      )}
    </div>
  )
}
