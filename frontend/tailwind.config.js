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
          bg: "#0a0e13",
          card: "#151a21",
          border: "#232a34",
          accent: "#00d395",
          accent2: "#00b7eb",
          bear: "#ff4b4b",
          bull: "#00d395"
        }
      }
    },
  },
  plugins: [],
}
