---
title: "发文基线说明（站点维护用）"
description: "AI 订阅攻略站的文章 frontmatter、分类标签和 shortcodes 使用规范。"
date: 2026-04-10
lastmod: 2026-04-10
draft: true
---

## 新文章 frontmatter 模板

```yaml
---
title: "这里写标题"
description: "这里写 1 句话摘要描述"
date: 2026-04-10
lastmod: 2026-04-10
summary: "列表页展示摘要"
tags: ["ChatGPT充值", "Claude Pro"]
categories: ["教程"]
showTableOfContents: true
showReadingTime: true
showDateUpdated: true
---
```

## 分类命名

- 教程
- 工具
- 支付
- 合租

## 推荐标签

- ChatGPT充值
- Claude Pro
- 虚拟卡
- 账号购买
- AI工具测评

## Shortcodes 用法

### 步骤卡片

```go-html-template
{{< steps-card step="1" title="步骤标题" tip="可选提示" >}}
这里写步骤说明。
{{< /steps-card >}}
```

### 对比表格

```go-html-template
{{< compare-table leftTitle="方案A" rightTitle="方案B" leftPros="优点1|优点2" rightPros="优点1|优点2" >}}
```

### 警告框

```go-html-template
{{< warning-box title="风险提醒" level="danger" >}}
这里写风险提示信息。
{{< /warning-box >}}
```

`level` 支持：`warning`（默认）、`danger`、`info`。
