/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./acc/templates/**/*.html",
    "./acc/static/src/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2563eb',
        'secondary': '#64748b',
        'success': '#16a34a',
        'danger': '#dc2626',
        'warning': '#f59e0b',
      }
    },
  },
  plugins: [],
}