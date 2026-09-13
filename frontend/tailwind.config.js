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
          bg2: "#1C1C1E",
          card: "rgba(28,28,30,0.72)",
          cardSolid: "#1C1C1E",
          cardHover: "rgba(44,44,46,0.80)",
          border: "rgba(255,255,255,0.08)",
          borderLight: "rgba(255,255,255,0.12)",
          separator: "rgba(60,60,67,0.33)",
          accent: "#0A84FF",
          accent2: "#5E5CE6",
          accent3: "#64D2FF",
          bear: "#FF453A",
          bull: "#30D158",
          warning: "#FF9F0A",
          muted: "#8E8E93"
        },
        ios: {
          blue: "#007AFF",
          blueDark: "#0A84FF",
          green: "#34C759",
          greenDark: "#30D158",
          indigo: "#5856D6",
          indigoDark: "#5E5CE6",
          orange: "#FF9500",
          orangeDark: "#FF9F0A",
          pink: "#FF2D55",
          pinkDark: "#FF375F",
          purple: "#AF52DE",
          purpleDark: "#BF5AF2",
          red: "#FF3B30",
          redDark: "#FF453A",
          teal: "#5AC8FA",
          tealDark: "#64D2FF",
          yellow: "#FFCC00",
          yellowDark: "#FFD60A",
          gray: "#8E8E93",
          gray2: "#AEAEB2",
          gray3: "#C7C7CC",
          gray4: "#D1D1D6",
          gray5: "#E5E5EA",
          gray6: "#F2F2F7",
          background: "#F2F2F7",
          backgroundDark: "#000000",
          groupedBackground: "#F2F2F7",
          groupedBackgroundDark: "#000000",
          secondaryBackground: "#FFFFFF",
          secondaryBackgroundDark: "#1C1C1E",
          tertiaryBackground: "#FFFFFF",
          tertiaryBackgroundDark: "#2C2C2E",
        },
        liquid: {
          bg: "rgba(255,255,255,0.72)",
          bgDark: "rgba(28,28,30,0.72)",
          bgStrong: "rgba(255,255,255,0.85)",
          bgStrongDark: "rgba(44,44,46,0.85)",
          border: "rgba(0,0,0,0.08)",
          borderDark: "rgba(255,255,255,0.12)",
          borderStrong: "rgba(0,0,0,0.12)",
          borderStrongDark: "rgba(255,255,255,0.18)",
        }
      },
      fontFamily: {
        sans: ["-apple-system", "SF Pro Display", "SF Pro Text", "Geist", "Inter", "system-ui", "sans-serif"],
        display: ["-apple-system", "SF Pro Display", "Geist", "system-ui", "sans-serif"],
        text: ["-apple-system", "SF Pro Text", "Geist", "Inter", "system-ui", "sans-serif"],
        mono: ['SF Mono', 'JetBrains Mono', 'Menlo', 'monospace'],
        sf: ["-apple-system", "SF Pro Display", "SF Pro Text", "system-ui", "sans-serif"],
      },
      borderRadius: {
        'ios': '20px',
        'ios-sm': '12px',
        'ios-lg': '28px',
        'ios-xl': '34px',
        'ios-pill': '999px',
        'clay': '20px',
        'clay-sm': '12px',
        'clay-lg': '28px',
      },
      boxShadow: {
        'ios': '0 4px 16px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.6)',
        'ios-dark': '0 8px 32px rgba(0,0,0,0.40), 0 2px 8px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.15)',
        'ios-lg': '0 12px 40px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.8)',
        'ios-lg-dark': '0 16px 48px rgba(0,0,0,0.50), 0 4px 16px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.18)',
        'liquid': '0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.7), inset 0 -1px 0 rgba(0,0,0,0.04)',
        'liquid-dark': '0 12px 40px rgba(0,0,0,0.40), 0 4px 12px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.3)',
        'liquid-strong': '0 16px 48px rgba(0,0,0,0.12), 0 6px 16px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.8)',
        'liquid-strong-dark': '0 20px 60px rgba(0,0,0,0.50), 0 8px 20px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.18)',
        'clay-light': '0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.7)',
        'clay-dark': '0 12px 40px rgba(0,0,0,0.40), 0 4px 12px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ticker': 'ticker 60s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 6s cubic-bezier(0.32,0.72,0,1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'liquid-float': 'liquidFloat 8s cubic-bezier(0.32,0.72,0,1) infinite',
        'ios-spring': 'iosSpring 0.6s cubic-bezier(0.2,0.8,0.2,1)',
      },
      keyframes: {
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' }
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(10,132,255,0.2)' },
          '100%': { boxShadow: '0 0 30px rgba(10,132,255,0.4)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0) translateZ(0)' },
          '50%': { transform: 'translateY(-8px) translateZ(0)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' }
        },
        liquidFloat: {
          '0%, 100%': { transform: 'translateY(0) translateX(0) scale(1) translateZ(0)' },
          '33%': { transform: 'translateY(-10px) translateX(5px) scale(1.02) translateZ(0)' },
          '66%': { transform: 'translateY(5px) translateX(-5px) scale(0.98) translateZ(0)' }
        },
        iosSpring: {
          '0%': { transform: 'scale(0.96) translateZ(0)', opacity: '0' },
          '100%': { transform: 'scale(1) translateZ(0)', opacity: '1' }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'ios-mesh': 'radial-gradient(at 20% 20%, rgba(0,122,255,0.08) 0%, transparent 50%), radial-gradient(at 80% 20%, rgba(88,86,214,0.08) 0%, transparent 50%), radial-gradient(at 50% 80%, rgba(52,199,89,0.06) 0%, transparent 50%)',
        'ios-mesh-dark': 'radial-gradient(at 20% 20%, rgba(10,132,255,0.15) 0%, transparent 50%), radial-gradient(at 80% 20%, rgba(94,92,230,0.12) 0%, transparent 50%), radial-gradient(at 50% 80%, rgba(48,209,88,0.10) 0%, transparent 50%)',
      },
      backdropBlur: {
        'ios': '40px',
        'ios-strong': '60px',
        'ios-thin': '20px',
      }
    },
  },
  plugins: [],
}
