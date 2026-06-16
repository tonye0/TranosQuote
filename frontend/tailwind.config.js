/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#1f4e78',
          600: '#1a4266',
          700: '#153654',
        },
      },
    },
  },
  plugins: [],
}
