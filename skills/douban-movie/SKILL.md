---
name: douban-movie
description: |
  查看豆瓣电影详情、Top250、正在热映。当用户想了解某部电影的评分、简介、演员信息，或浏览电影排行榜时使用。
---

# 规则

**只用下面的 python3 命令，禁止使用 curl 或其他方式。**

`P` 代表 `python3 ~/.openclaw/skills/douban/scripts/douban_client.py`。

# 命令

| 功能 | 命令 |
|------|------|
| 电影详情 | `P movie <subject_id>` |
| 电影 Top250 | `P top250` |
| 正在热映 | `P now-playing` |

# 展示格式

电影详情展示：片名、年份、评分、导演、主演、类型、剧情简介。Top250 展示序号、片名、评分、经典语录。
