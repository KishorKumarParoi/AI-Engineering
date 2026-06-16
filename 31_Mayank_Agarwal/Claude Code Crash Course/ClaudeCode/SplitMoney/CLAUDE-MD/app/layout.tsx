import type { Metadata } from 'next'
import { JobApplicationsProvider } from '@/lib/context'
import { ThemeProvider } from '@/lib/theme-provider'
import './globals.css'

export const metadata: Metadata = {
  title: 'Job Application Tracker',
  description: 'Track your job applications with ease',
}

const themeInitScript = `
  const stored = localStorage.getItem('job-tracker-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const resolved = stored === 'dark' || ((!stored || stored === 'system') && prefersDark);
  if (resolved) {
    document.documentElement.classList.add('dark');
    document.documentElement.style.colorScheme = 'dark';
  } else {
    document.documentElement.style.colorScheme = 'light';
  }
`

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeInitScript }}
          suppressHydrationWarning
        />
      </head>
      <body className="bg-slate-50 dark:bg-slate-950 transition-colors">
        <ThemeProvider>
          <JobApplicationsProvider>{children}</JobApplicationsProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
