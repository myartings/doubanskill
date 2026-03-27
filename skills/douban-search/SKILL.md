---
name: douban-search
description: |
  搜索豆瓣内容。当用户想搜索豆瓣上的电影、图书、音乐、小组时使用。
---

# 规则

**只用下面的 python3 命令，禁止使用 curl 或其他方式。**

`P` 代表 `python3 <SKILL_DIR>/scripts/douban_client.py`（SKILL_DIR：`${CLAUDE_PLUGIN_ROOT}` 或 `~/.openclaw/skills/douban` 或 `~/.claude/skills/douban`，取存在的路径）。

# 命令

| 功能 | 命令 |
|------|------|
| 综合搜索 | `P search "关键词"` |
| 搜索电影 | `P search-movie "关键词"` |
| 搜索图书 | `P search-book "关键词"` |
| 搜索音乐 | `P search-music "关键词"` |
| 搜索小组 | `P search-group "关键词"` |

# 展示格式

搜索结果包含电影、图书、音乐、小组等。每条结果展示：类型标签、标题、摘要、链接。简洁展示，默认展示 15 条。
