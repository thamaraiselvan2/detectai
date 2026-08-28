/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#070b14",
          card: "#0d1527",
          panel: "#111c35",
          border: "#1e293b",
          primary: "#00f0ff",
          secondary: "#7928ca",
          accent: "#38bdf8",
          low: "#10b981",
          medium: "#f59e0b",
          high: "#f97316",
          critical: "#ef4444"
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
      },
      boxShadow: {
        'glow-cyan': '0 0 25px -5px rgba(0, 240, 255, 0.3)',
        'glow-red': '0 0 25px -5px rgba(239, 68, 68, 0.4)',
        'glow-amber': '0 0 25px -5px rgba(245, 158, 11, 0.3)',
        'glow-green': '0 0 25px -5px rgba(16, 185, 129, 0.3)',
      }
    },
  },
  plugins: [],
}
