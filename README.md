# Content Site Template (Hugo + Blowfish)

一个可直接复用的内容网站模板，仅保留核心主题配置与基础内容骨架，适合快速搭建中英双语内容站。

## 1. 模板包含什么

- Hugo + Blowfish（通过 Hugo Module 引入）
- 双语配置（`en` / `zh-cn`）
- 基础栏目：首页、文章、标签、分类、关于
- 3 套可切换配色方案
- SEO 基础项（robots、sitemap、Open Graph 默认图、Search Console 与 GA4 配置位）

## 2. 快速启动

```bash
cd /Users/zhangjane/home_work_space/content-site-template
hugo server
```

首次建议先检查环境：

```bash
go version
hugo version
hugo mod graph
```

## 3. 必改配置（上线前）

### 3.1 站点地址

编辑 `hugo.toml`：

```toml
baseURL = "https://example.com/"
```

改成你的正式域名，如 `https://docs.yourdomain.com/`。

### 3.2 站点名称与作者信息

编辑：

- `config/_default/languages.en.toml`
- `config/_default/languages.zh-cn.toml`

重点字段：

- `title`
- `description`
- `[params.author]` 下的 `name`、`headline`、`bio`、`links`

### 3.3 导航菜单

编辑：

- `config/_default/menus.en.toml`
- `config/_default/menus.zh-cn.toml`

可按你的内容结构增删菜单项。

## 4. 主题与颜色配置

主题主配置在 `config/_default/params.toml`。

### 4.1 切换配色方案

```toml
colorScheme = "chatgptnews"
```

可选值：

- `chatgptnews`
- `chatgptnews-dark`
- `chatgptnews-soft`

对应文件：

- `assets/css/schemes/chatgptnews.css`
- `assets/css/schemes/chatgptnews-dark.css`
- `assets/css/schemes/chatgptnews-soft.css`

### 4.2 自定义主题细节

编辑 `assets/css/custom.css` 可覆盖默认视觉效果（背景、按钮、卡片细节等）。

### 4.3 首页布局

编辑 `config/_default/params.toml` 的 `[homepage]`：

```toml
[homepage]
layout = "hero"
showRecent = true
showRecentItems = 6
cardView = true
```

常用 `layout`：`hero`、`card`、`page`、`profile`。

## 5. SEO 配置

## 5.1 全站基础 SEO

编辑 `config/_default/hugo.toml`：

- `enableRobotsTXT = true`
- `[sitemap]`（`changefreq`、`priority`）
- `[outputs] home = ["HTML", "RSS", "JSON"]`

## 5.2 页面级 SEO（文章 Front Matter）

每篇文章建议至少包含：

```yaml
---
title: "Your article title"
date: 2026-04-10T12:00:00+08:00
description: "Meta description for search results"
summary: "Short summary shown in list/card"
tags: ["tag-1", "tag-2"]
categories: ["category-1"]
---
```

## 5.3 Search Console 与 Analytics

编辑 `config/_default/params.toml`：

```toml
[verification]
google = ""

[analytics]
  [analytics.ga4]
  id = ""
```

填入你的 Search Console 验证码与 GA4 Measurement ID。

## 6. 新增文章（双语）

建议同一主题建立两篇：

- `content/articles/your-topic.en.md`
- `content/articles/your-topic.zh-cn.md`

并在 front matter 中保持一致的结构和 SEO 字段。

## 7. 构建与发布

本地构建：

```bash
hugo
```

产物在 `public/`。

部署可选：

- GitHub Pages（推荐）
- Netlify / Vercel
- 自托管静态服务器

## 8. 推送到 GitHub（新仓库）

```bash
cd /Users/zhangjane/home_work_space/content-site-template
git init
git add .
git commit -m "init: content site template"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## 9. 常见问题

### Blowfish 模块加载失败

确保 `config/_default/module.toml` 为：

```toml
[[imports]]
path = "github.com/nunocoracao/blowfish/v2"
```

并且未在 `hugo.toml` 中设置 `theme = "blowfish"`（避免被当作本地主题目录）。
