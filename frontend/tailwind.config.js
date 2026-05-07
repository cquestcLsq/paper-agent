/** @type {import('tailwindcss').Config} */
export default {
  // -------- 扫描哪些文件中的 Tailwind 类名 --------
  content: [
    "./index.html",
    "./src/**/*.{vue,js}",  // 所有 Vue 组件和 JS 文件
  ],
  theme: {
    extend: {},  // 可在此扩展自定义颜色、字号等
  },
  plugins: [],
}