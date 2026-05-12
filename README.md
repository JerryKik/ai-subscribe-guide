# AI 订阅攻略站（Hugo + Blowfish）

面向国内用户的 AI 服务订阅与支付类内容站源码，基于 Hugo 与 Blowfish 主题，并配套 Agent Skills（选题 → 写作 → 质检 → 发布流程）。

## 1. 项目包含什么

- Hugo Extended + Blowfish（通过 Hugo Module 引入）
- 当前默认语言为 **简体中文**（`zh-cn`；配置中已禁用 `en`，可按需重新启用）
- 内容结构：文章、标签、分类、关于、免责声明等（见 `content/`）
- 多套可切换配色方案（见 `assets/css/schemes/`）
- SEO 基础项（robots、sitemap、Open Graph 默认图、Search Console 与 GA4 配置位）
- Agent Skills：`.agents/skills/`（关键词、写作、质检、`generate-blog-workflow` 与脚本）

### 1.1 Agent Skills 入口

路径：`.agents/skills/`

- `blog-seo-keyword-select`：关键词与选题扩展
- `blog-seo-content-create`：正文写作（观点、结构、语气）
- `blog-seo-content-check`：文章发布前量化检查
- `generate-blog-workflow`：文件命名、frontmatter、多语言与发布流程
- `scripts/`：检查流程脚本（含 `article_seo_eval.py`）

推荐顺序：`blog-seo-keyword-select` → `blog-seo-content-create` → `blog-seo-content-check` → `generate-blog-workflow`。

说明文档：

- `CLAUDE.md`：技能索引与默认工作流
- `AGENTS.md`：指向 `CLAUDE.md`

## 2. 本地运行

在项目根目录执行：

```bash
cd /path/to/ai-subscribe-guide
hugo server
```

首次建议确认环境（**Hugo Extended 建议与 CI 一致：0.159.1**，见 `.github/workflows/hugo.yml` 中的 `HUGO_VERSION`）：

```bash
go version
hugo version
hugo mod graph
```

## 3. 上线前必改配置

### 3.1 站点地址（baseURL）

编辑**仓库根目录**的 `hugo.toml`（目前仅含 `baseURL`）：

```toml
baseURL = "https://你的域名/"
```

若使用 **GitHub Pages** 默认地址，一般为 `https://<用户名>.github.io/<仓库名>/`（注意末尾斜杠与路径是否与仓库名一致）。推送后也可在 GitHub 仓库 **Settings → Pages** 中查看实际站点 URL，并与 `baseURL` 对齐。

### 3.2 站点名称与作者

编辑 `config/_default/languages.zh-cn.toml`：

- `title`、`description`
- `[params.author]` 下的 `headline`、`bio`（以及按需取消注释 `name`、`links`）

若启用英文，再维护 `languages.en.toml` 并与 `config/_default/hugo.toml` 中的 `disableLanguages` 配合调整。

### 3.3 导航菜单

主要编辑 `config/_default/menus.zh-cn.toml`（若启用英文则同时维护 `menus.en.toml`）。

## 4. 主题与配色

主题参数在 `config/_default/params.toml`。当前默认：

```toml
colorScheme = "guideclean"
```

可选配色（对应 `assets/css/schemes/` 下的文件）包括但不限于：

- `guideclean`、`guideclean-dark`、`guideclean-soft`
- `chatgptnews`、`chatgptnews-dark`、`chatgptnews-soft`

自定义样式可编辑 `assets/css/custom.css`。

### 4.1 首页布局

在 `config/_default/params.toml` 的 `[homepage]` 中调整，例如：

```toml
[homepage]
layout = "hero"
showRecent = true
showRecentItems = 6
cardView = true
```

常用 `layout`：`hero`、`card`、`page`、`profile`。

## 5. SEO 配置

### 5.1 全站基础 SEO

编辑 `config/_default/hugo.toml`：

- `enableRobotsTXT`
- `[sitemap]`
- `[outputs]` 中 `home` 包含 `HTML`、`RSS`、`JSON` 等

### 5.2 文章 Front Matter

建议每篇文章至少包含：

```yaml
---
title: "文章标题"
date: 2026-04-10T12:00:00+08:00
description: "搜索结果摘要"
summary: "列表/卡片摘要"
tags: ["标签一", "标签二"]
categories: ["分类"]
---
```

### 5.3 Search Console 与 Analytics

两者由 Blowfish 的 `layouts/partials/head.html` 与 `partials/analytics/main.html` 读取，**配置位置不同**（与 Hugo 是否提供内置项有关）：

**Google Search Console（HTML 标签验证）** — 写在 `config/_default/params.toml` 的 `[verification]`，值为 Search Console「HTML 标签」里 `content="..."` 中的字符串：

```toml
[verification]
google = "你的验证码"
```

可选：`bing`、`pinterest`、`yandex`、`fediverse` 等键，与主题 `head` 模板一致。

**Google Analytics 4** — 使用 Hugo 官方 `[services.googleAnalytics]`，写在 `config/_default/hugo.toml`（不要写在 `params.toml` 的 `[analytics.ga4]`，当前主题不会读取）：

```toml
[services.googleAnalytics]
id = "G-XXXXXXXXXX"
```

**本地预览**：主题仅在 **生产环境** 注入 GA 脚本（`hugo.IsProduction`）。默认 `hugo server` 为开发环境，页面里看不到 gtag；需要本地验证时可执行 `hugo server -e production`。正式部署执行 `hugo` 时为生产构建，会包含统计脚本（前提是已配置 `id`）。

## 6. 新增文章

当前以中文为主，文章可放在 `content/articles/`，例如 `某主题.zh-cn.md`。若启用多语言，可为同一主题维护多份语言文件并在 frontmatter 中用 `translationKey` 关联（详见 `generate-blog-workflow` 技能）。

## 7. 构建产物

本地构建：

```bash
hugo
```

静态站点输出目录为 `public/`。

## 8. GitHub Pages 自动部署

本仓库提供与参考项目同结构的 GitHub Actions 工作流：`.github/workflows/hugo.yml`（构建与缓存步骤与 `peaceiris/actions-hugo`、`actions/configure-pages`、`actions/deploy-pages` 标准 Pages 流程一致）。

**首次启用步骤：**

1. 将代码推送到 GitHub 的 `main` 分支。
2. 打开仓库 **Settings → Pages**。
3. **Build and deployment** 的 **Source** 选择 **GitHub Actions**（不要选「Deploy from a branch」的旧方式，除非你有意自行维护）。
4. 在 **Actions** 中确认 **Deploy Hugo site to Pages** 运行成功；完成后 Pages 设置页会显示站点 URL。

工作流要点：

- 使用 Hugo Extended **0.159.1**（与 `HUGO_VERSION` 一致；升级时同步修改 `.github/workflows/hugo.yml` 与本文说明，并在本地验证）。
- 构建命令：`hugo --gc --minify`，并使用 `configure-pages` 输出的 `base_url` 作为 `--baseURL`，与 GitHub Pages 域名一致。
- 缓存 `~/.cache/hugo_cache` 与 `~/go/pkg/mod`，依赖 `go.sum` 与 `config/_default/module.toml` 的哈希。

也可将同一套静态文件部署到 Netlify、Vercel 或任意静态托管；只需在对应平台配置 `hugo` 构建命令与 `public` 输出目录即可。

## 9. 推送到 GitHub（新仓库）

```bash
cd /path/to/ai-subscribe-guide
git init
git add .
git commit -m "init: ai-subscribe-guide"
git branch -M main
git remote add origin <你的仓库地址>
git push -u origin main
```

按需将 `go.mod` 第一行的 `module` 路径改为你的模块路径（不影响 GitHub Pages 部署，但与 Go module 缓存标识相关）。

## 10. 常见问题

### Blowfish 模块拉取失败

确认 `config/_default/module.toml` 包含：

```toml
[[imports]]
path = "github.com/nunocoracao/blowfish/v2"
```

且不要在根 `hugo.toml` 中设置 `theme = "blowfish"`（避免被当作本地主题目录）。网络受限时可配置 Go 代理或使用 vendor（按 Hugo 文档操作）。

### 本地与 CI 的 Hugo 版本不一致

以 `.github/workflows/hugo.yml` 中的 `HUGO_VERSION`（当前 **0.159.1**）为准，本地请使用相同的 **Hugo Extended** 版本，避免构建差异。
