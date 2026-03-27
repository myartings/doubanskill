---
name: douban-book
description: |
  查看豆瓣图书详情。当用户想了解某本书的评分、简介、作者信息时使用。
---

# 规则

**只用下面的 python3 命令，禁止使用 curl 或其他方式。**

`P` 代表 `python3 <SKILL_DIR>/scripts/douban_client.py`（SKILL_DIR：`${CLAUDE_PLUGIN_ROOT}` 或 `~/.openclaw/skills/douban` 或 `~/.claude/skills/douban`，取存在的路径）。

# 命令

| 功能 | 命令 |
|------|------|
| 图书详情 | `P book <subject_id>` |

# 展示格式

图书详情展示：书名、评分、作者、出版社、出版年、内容简介、标签。
