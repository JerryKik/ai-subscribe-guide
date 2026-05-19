# 线上页面 SEO 检测（`check-page.py`）

对已发布或预览中的 **HTML 页面**做页面级 SEO 机械检测，输出结构化 JSON，供 Agent 消费。  
与 `article_seo_eval.py`（Markdown 正文结构）和 `td_frontmatter_check.py`（frontmatter TD 长度）**职责互补**。

---

## 1. 何时使用

| 场景 | 工具 |
|------|------|
| 草稿 Markdown 结构 / 密度 | `article_seo_eval.py` |
| frontmatter `title` / `description` 长度 | `td_frontmatter_check.py` |
| 线上或预览 URL 的 `<title>`、H1、meta、canonical、slug | **`check-page.py`** |

发布前或改版后：用 `--keyword` 核对核心词是否出现在 H1、title、meta、URL slug。

---

## 2. 快速命令

```bash
# 安装依赖（建议在 venv 中）
python3 -m pip install -r .agents/skills/scripts/requirements-seo-check.txt

# 单页检测（JSON 输出到 stdout）
python3 .agents/skills/scripts/check-page.py https://example.com/blog/my-post

# 指定核心词 + 超时
python3 .agents/skills/scripts/check-page.py \
  https://example.com/blog/my-post \
  --keyword "ChatGPT Plus" \
  --timeout 30

# 自定义 TD 阈值文件（默认读取 td_check_defaults.json）
python3 .agents/skills/scripts/check-page.py \
  https://example.com/ \
  --defaults .agents/skills/scripts/td_check_defaults.json
```

---

## 3. 检测项

| 字段 | 机械检测（脚本） | 需 LLM 复核（`llm_review_required`） |
|------|------------------|--------------------------------------|
| `h1` | 数量=1、非空、长度、关键词字符串匹配 | `keyword_match=partial` 时语义是否覆盖意图 |
| `title` | 存在、长度（站点 40–60）、关键词位置 | 语法自然、partial 匹配语义 |
| `meta_description` | 存在、长度（站点 140–160）、关键词匹配 | 句式、具体收益、非堆砌（有内容时恒为 true） |
| `canonical` | 是否存在、是否与最终 URL 一致 | — |
| `url_slug` | 小写、连字符、停用词、重复词、段长 | 关键词意图、层级是否合理 |

`summary.overall`：`pass` | `warn` | `fail`（任一子项 `fail` 则整体 `fail`）。

---

## 4. 退出码

| 条件 | 退出码 |
|------|--------|
| 抓取失败、非 200、空 body | 1 |
| `summary.overall == fail` | 1 |
| 仅有 `warn` 或全部 `pass` | 0 |

---

## 5. 与站点 TD 规则对齐

长度阈值默认来自 **`td_check_defaults.json`**（与 [seo_frontmatter.md](../generate-blog-workflow/references/seo_frontmatter.md) 一致）：

- `title`：40–60 字符（Unicode `len`）
- `meta description`：140–160 字符

线上 `<title>` / meta 可能与 Hugo frontmatter 不同（主题模板、SEO 插件）；两者都应检查。

---

## 6. 安全说明

- 仅允许 `http://` / `https://` URL
- 解析 hostname 后拦截内网 / 回环 / 保留 IP（SSRF 防护）
- 最多跟随 5 次重定向

---

## 7. 输出示例（节选）

```json
{
  "url": "https://example.com/blog/best-shoes",
  "final_url": "https://example.com/blog/best-shoes/",
  "http_status": 200,
  "summary": {
    "overall": "warn",
    "checks": {
      "url_slug": "pass",
      "title": "pass",
      "meta_description": "warn",
      "h1": "pass",
      "canonical": "pass"
    },
    "llm_review_required": true,
    "llm_review_fields": ["meta_description"]
  },
  "h1": {
    "status": "pass",
    "keyword_match": "full",
    "llm_review_required": false
  }
}
```
