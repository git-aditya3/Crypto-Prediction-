/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        crypto: {
          bg: "#000000",
          bg2: "#0a0e13",
          card: "rgba(28,28,30,0.7)",
          cardHover: "rgba(38,38,40,0.8)",
          border: "rgba(255,255,255,0.08)",
          borderLight: "rgba(255,255,255,0.12)",
          accent: "#00d395",
          accent2: "#6366f1",
          accent3: "#06b6d4",
          bear: "#ff4b4b",
          bull: "#00d395",
          warning: "#f59e0b",
          muted: "#9CA3AF"
        },
        clay: {
          light: {
            canvas1: "#FFCFDF",
            canvas2: "#BBE1FA",
            card: "#ffffff",
            text: "#1e293b",
            muted: "#64748b",
            border: "rgba(255,255,255,0.4)"
          },
          dark: {
            canvas: "#000000",
            card: "rgba(28,28,30,0.7)",
            cardSolid: "#1c1c1e",
            text: "#F3F4F6",
            muted: "#9CA3AF",
            border: "rgba(255,255,255,0.08)"
          }
        }
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'Quicksand', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        poppins: ['Poppins', 'sans-serif'],
        quicksand: ['Quicksand', 'sans-serif'],
      },
      borderRadius: {
        'clay': '32px',
        'clay-sm': '24px',
        'clay-lg': '40px',
      },
      boxShadow: {
        'clay-light': '0px 20px 40px rgba(31, 38, 135, 0.08), inset 6px 6px 12px rgba(255, 255, 255, 0.9), inset -6px -6px 12px rgba(0, 0, 0, 0.1)',
        'clay-dark': '0px 20px 40px rgba(0, 0, 0, 0.6), inset 4px 4px 8px rgba(255, 255, 255, 0.12), inset -4px -4px 8px rgba(0, 0, 0, 0.5)',
        'clay-light-hover': '0px 24px 48px rgba(31, 38, 135, 0.12), inset 6px 6px 12px rgba(255, 255, 255, 0.95), inset -6px -6px 12px rgba(0, 0, 0, 0.08)',
        'clay-dark-hover': '0px 24px 48px rgba(0, 0, 0, 0.7), inset 4px 4px 8px rgba(255, 255, 255, 0.2), inset -4px -4px 8px rgba(0, 0, 0, 0.6)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ticker': 'ticker 60s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'clay-float': 'clayFloat 4s ease-in-out infinite',
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
        },
        clayFloat: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'clay-light-canvas': 'linear-gradient(135deg, #FFCFDF 0%, #BBE1FA 100%)',
        'clay-dark-canvas': 'linear-gradient(135deg, #000000 0%, #000000 100%)',
      }
    },
  },
  plugins: [],
}
