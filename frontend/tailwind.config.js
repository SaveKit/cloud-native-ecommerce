/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // <-- นี่คือส่วนที่เราต้องแก้อยู่แล้ว
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}