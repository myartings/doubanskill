---
name: douban-comments
description: |
  查看豆瓣电影/图书的短评和长评。当用户想看某部电影或某本书的评价、评论时使用。
---

# 规则

**只用下面的 python3 命令，禁止使用 curl 或其他方式。**

`P` 代表 `python3 ~/.openclaw/skills/douban/scripts/douban_client.py`。

# 命令

| 功能 | 命令 |
|------|------|
| 电影短评 | `P movie-comments <subject_id>` |
| 图书短评 | `P book-comments <subject_id>` |
| 影评 | `P reviews movie <subject_id>` |
| 书评 | `P reviews book <subject_id>` |

# 展示格式

短评展示：用户名、星级、评论内容、有用数。影评/书评展示：标题、评分、作者、摘要、链接。
