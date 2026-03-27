# Douban Skill

豆瓣 OpenClaw Skill。

## 架构

- 纯 Python 3 标准库，无第三方依赖
- 电影/图书详情使用移动端页面 (`m.douban.com`)，无 PoW 反爬
- 桌面端页面内置 SHA-512 PoW 解算器（Top250、热映、短评等）
- 搜索使用 DuckDuckGo + 豆瓣 suggest API 双通道
- CLI 客户端：`scripts/douban_client.py`

## 项目结构

```
├── SKILL.md                         # OpenClaw 根 skill
├── CLAUDE.md                        # 架构文档（本文件）
├── skills/                          # 5 个子 skill
│   ├── douban-search/SKILL.md
│   ├── douban-movie/SKILL.md
│   ├── douban-book/SKILL.md
│   ├── douban-comments/SKILL.md
│   └── douban-user/SKILL.md
├── scripts/douban_client.py         # 豆瓣客户端
├── scripts/setup.sh                 # 初始化脚本
```

## 豆瓣反爬注意事项

- 桌面端（movie.douban.com 等）有 JavaScript PoW 挑战：页面返回 `<form>` 带 `tok`/`cha` 字段，需计算 SHA-512 nonce 使 hash 前 4 位为零，POST 到 `/c` 获取通行 cookie
- 移动端（m.douban.com）无 PoW，电影/图书详情优先走移动端
- 必须带合理的 User-Agent，否则直接 403
- 频繁请求会触发限流，建议间隔访问
- Cookie 文件格式：JSON 数组（来自 Cookie-Editor 浏览器扩展）

## 数据来源

| 功能 | 数据来源 | 需要 Cookie |
|------|----------|-------------|
| search | DuckDuckGo | 否 |
| search-movie/book | suggest API (`/j/subject_suggest`) | 否 |
| movie/book 详情 | m.douban.com 移动端页面 | 否 |
| top250 | movie.douban.com 桌面端 + PoW | 否 |
| now-playing | movie.douban.com 桌面端 + PoW | 否 |
| movie/book-comments | 桌面端页面 + PoW | 是 |
| reviews | m.douban.com 移动端页面 | 否 |
| user | 桌面端页面 + PoW | 是 |

## 添加新功能

1. 在 `douban_client.py` 中添加 `cmd_xxx()` 函数
2. 在 `main()` 的 `commands` 字典中注册
3. 更新 `SKILL.md` 命令表
4. 如需新的子 skill，在 `skills/` 下创建目录和 `SKILL.md`
5. 测试：`python3 scripts/douban_client.py xxx <args>`
