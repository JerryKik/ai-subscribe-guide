# Repository Collaboration Guide (Workspace Agent)

This template is designed for quickly building a **Hugo + Blowfish** multilingual content site.

## What this file is for

- A **skill index** and **task routing** guide for agents working in this repo.
- A default, repeatable workflow to go from idea → draft → quality gate → publish.

## Default content workflow (recommended order)

1. **Keyword & intent**: `.agents/skills/blog-seo-keyword-select/SKILL.md`
2. **Draft writing (voice & structure)**: `.agents/skills/blog-seo-content-create/SKILL.md`
3. **Post-draft checks (quantitative gate)**: `.agents/skills/blog-seo-content-check/SKILL.md`
4. **File naming / frontmatter / multilingual / build validation**: `.agents/skills/generate-blog-workflow/SKILL.md`

## Skills included in this template

- `.agents/skills/blog-seo-keyword-select/`
- `.agents/skills/blog-seo-content-create/`
- `.agents/skills/blog-seo-content-check/`
- `.agents/skills/generate-blog-workflow/`
- `.agents/skills/scripts/` (helpers such as `article_seo_eval.py`)

## Hugo site “core config” locations

- **Site config**: `config/_default/`
- **Theme module**: `config/_default/module.toml`
- **Theme params**: `config/_default/params.toml`
- **Menus**: `config/_default/menus.*.toml`
- **Languages**: `config/_default/languages.*.toml`
- **Custom styling**: `assets/css/custom.css` and `assets/css/schemes/*.css`

## Build validation

```bash
cd /Users/zhangjane/home_work_space/content-site-template
hugo
hugo server
```

