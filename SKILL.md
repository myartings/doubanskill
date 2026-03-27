---
name: douban
description: |
  豆瓣（Douban）搜索助手。通过 Python 命令搜索豆瓣：搜索电影/图书/音乐/小组、查看条目详情、查看评论、查看用户、浏览排行榜。
  当用户提到豆瓣、Douban、豆瓣搜索、豆瓣电影、豆瓣读书、豆瓣音乐、豆瓣评分、搜豆瓣、豆瓣上怎么说等关键词时使用。
---

# 规则

1. **只用下面的 python3 命令。禁止用 curl、wget、httpie 或任何其他方式。**
2. 首次使用先运行初始化：`cd ~/.openclaw/skills/douban && bash scripts/setup.sh`
3. 部分功能需要登录 Cookie，未登录时先引导用户导入 Cookie

# 命令

以下是全部可用命令，`P` 代表 `python3 ~/.openclaw/skills/douban/scripts/douban_client.py`。

## 无需登录

| 功能 | 命令 |
|------|------|
| 搜索（综合） | `P search "关键词"` |
| 搜索电影 | `P search-movie "关键词"` |
| 搜索图书 | `P search-book "关键词"` |
| 搜索音乐 | `P search-music "关键词"` |
| 搜索小组 | `P search-group "关键词"` |
| 电影详情 | `P movie <subject_id>` |
| 图书详情 | `P book <subject_id>` |
| 电影 Top250 | `P top250` |
| 正在热映 | `P now-playing` |

## 需要登录 Cookie

| 功能 | 命令 |
|------|------|
| 电影短评 | `P movie-comments <subject_id>` |
| 图书短评 | `P book-comments <subject_id>` |
| 影评/书评 | `P reviews <movie/book> <subject_id>` |
| 用户资料 | `P user <user_id>` |
| 导入 Cookie | `P import-cookies` |

# Cookie 导入

遇到 403 错误时，引导用户导入 Cookie：

1. 用浏览器登录 douban.com
2. 安装 Cookie-Editor 扩展，导出 JSON
3. 保存到 `~/.openclaw/skills/douban/cookies.json`

# 示例

```shell
# 搜索电影（无需登录）
python3 ~/.openclaw/skills/douban/scripts/douban_client.py search-movie "肖申克的救赎"

# 看电影详情（无需登录）
python3 ~/.openclaw/skills/douban/scripts/douban_client.py movie 1292052

# 电影 Top250（无需登录）
python3 ~/.openclaw/skills/douban/scripts/douban_client.py top250

# 综合搜索
python3 ~/.openclaw/skills/douban/scripts/douban_client.py search "三体"
```
