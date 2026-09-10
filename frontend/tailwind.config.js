/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0f19',
        card: '#111827',
        cardBorder: '#1e293b',
        primary: {
          DEFAULT: '#38bdf8',
          hover: '#0284c7',
          dark: '#0369a1',
          light: '#7dd3fc'
        },
        accent: '#818cf8',
        surface: '#1e293b',
        surfaceHover: '#334155'
      }
    },
  },
  plugins: [],
}
