/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0b0f1a',
          900: '#111827',
          700: '#374151',
          500: '#6b7280',
          200: '#e5e7eb',
          50: '#f8fafc',
        },
      },
      boxShadow: {
        panel: '0 1px 2px rgba(16,24,40,0.04), 0 8px 24px -12px rgba(16,24,40,0.18)',
      },
    },
  },
  plugins: [],
}
