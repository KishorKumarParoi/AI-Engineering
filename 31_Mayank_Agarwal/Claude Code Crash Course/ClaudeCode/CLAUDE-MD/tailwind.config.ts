import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        kanban: {
          wishlist: '#f1f5f9',
          applied: '#dbeafe',
          phoneScreen: '#f3e8ff',
          interviewing: '#fef3c7',
          offer: '#dcfce7',
          rejected: '#fee2e2',
          withdrawn: '#f3f4f6',
        },
      },
    },
  },
  plugins: [],
}

export default config
