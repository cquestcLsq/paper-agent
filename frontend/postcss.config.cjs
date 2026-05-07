// PostCSS 配置：处理 CSS 时依次调用 tailwindcss 和 autoprefixer
module.exports = {
  plugins: {
    tailwindcss: { config: './tailwind.config.js' },   // 扫描 JS/Vue 文件中的类名，生成对应 CSS
    autoprefixer: {},  // 自动添加浏览器前缀（-webkit- 等）
  },
}
