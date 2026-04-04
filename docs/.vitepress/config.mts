import { defineConfig } from "vitepress"

export default defineConfig({
  title: "KnowledgeRAG-GZHU",
  description: "工程治理与竞赛演示文档",
  lang: "zh-CN",
  themeConfig: {
    nav: [
      { text: "首页", link: "/" }
    ],
    sidebar: [
      {
        text: "工程文档",
        items: [{ text: "总览", link: "/" }]
      }
    ]
  }
})
