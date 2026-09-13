/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        crypto: {
          bg: "#060a0f",
          bg2: "#0a0e13",
          card: "#10161f",
          cardHover: "#151d2a",
          border: "#1e2a3a",
          borderLight: "#2a3a4f",
          accent: "#00d395",
          accent2: "#6366f1",
          accent3: "#06b6d4",
          bear: "#ff4b4b",
          bull: "#00d395",
          warning: "#f59e0b",
          muted: "#64748b"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ticker': 'ticker 60s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' }
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(0,211,149,0.2)' },
          '100%': { boxShadow: '0 0 30px rgba(0,211,149,0.4)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'radial-gradient(at 40% 20%, hsla(160,100%,50%,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(239,100%,70%,0.15) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(189,100%,50%,0.1) 0px, transparent 50%)',
      }
    },
  },
  plugins: [],
}
