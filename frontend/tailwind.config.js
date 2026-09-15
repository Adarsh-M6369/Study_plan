/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBase: '#080b11',         // Dark Color 1: Deep Abyss Black
        darkSurface: '#141b2d',      // Dark Color 2: Midnight Slate / Sapphire Charcoal
        darkSurfaceHover: '#1d273e',
        darkBorder: '#232f48',
        lightAccent: {               // Light Color: Luminous Sunburst Amber / Gold Light
          DEFAULT: '#fbbf24',
          hover: '#f59e0b',
          glow: '#fef08a',
          dark: '#b45309'
        }
      }
    },
  },
  plugins: [],
}
