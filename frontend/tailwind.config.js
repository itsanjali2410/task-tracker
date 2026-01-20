/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0F4C81',
          foreground: '#FFFFFF',
          hover: '#0D4270',
          active: '#0A365C'
        },
        secondary: {
          DEFAULT: '#F5A623',
          foreground: '#FFFFFF',
          hover: '#D99018'
        },
        background: {
          DEFAULT: '#F8FAFC',
          paper: '#FFFFFF',
          sidebar: '#0F172A'
        },
        text: {
          primary: '#0F172A',
          secondary: '#64748B',
          muted: '#94A3B8'
        },
        border: {
          DEFAULT: '#E2E8F0',
          focus: '#0F4C81'
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};
