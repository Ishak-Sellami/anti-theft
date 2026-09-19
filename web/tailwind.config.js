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
        background: '#0B1120',
        surface: '#151F32',
        surfaceHover: '#1E293B',
        border: '#1E293B',
        primary: {
          DEFAULT: '#38BDF8',
          hover: '#0284C7',
          muted: 'rgba(56, 189, 248, 0.15)',
        },
        stolen: {
          DEFAULT: '#EF4444',
          glow: 'rgba(239, 68, 68, 0.3)',
          muted: 'rgba(239, 68, 68, 0.15)',
        },
        protected: {
          DEFAULT: '#3B82F6',
          muted: 'rgba(59, 130, 246, 0.15)',
        },
        normal: {
          DEFAULT: '#10B981',
          muted: 'rgba(16, 185, 129, 0.15)',
        },
        recovery: {
          DEFAULT: '#F59E0B',
          muted: 'rgba(245, 158, 11, 0.15)',
        }
      },
    },
  },
  plugins: [],
}
