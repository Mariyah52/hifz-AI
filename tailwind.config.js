/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: 'var(--color-paper)',
        'paper-dim': 'var(--color-paper-dim)',
        ink: 'var(--color-ink)',
        'ink-soft': 'var(--color-ink-soft)',
        teal: {
          DEFAULT: 'var(--color-teal)',
          dark: 'var(--color-teal-dark)',
        },
        gold: 'var(--color-gold)',
        maroon: 'var(--color-maroon)',
        sage: 'var(--color-sage)',
      },
      fontFamily: {
        display: ['Fraunces', 'ui-serif', 'serif'],
        body: ['Inter', 'ui-sans-serif', 'sans-serif'],
        arabic: ['Amiri', 'Scheherazade New', 'serif'],
        'arabic-alt': ['Scheherazade New', 'Amiri', 'serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '1.25rem',
      },
      boxShadow: {
        folio: '0 1px 2px rgba(22, 48, 43, 0.06), 0 8px 24px -8px rgba(22, 48, 43, 0.12)',
      },
    },
  },
  plugins: [],
}
