#!/usr/bin/env python3
"""Douban (豆瓣) CLI Client.

Usage:
    python douban_client.py search <keyword>              # Search all (via DuckDuckGo)
    python douban_client.py search-movie <keyword>        # Search movies
    python douban_client.py search-book <keyword>         # Search books
    python douban_client.py search-music <keyword>        # Search music
    python douban_client.py search-group <keyword>        # Search groups
    python douban_client.py movie <subject_id>            # Movie detail
    python douban_client.py book <subject_id>             # Book detail
    python douban_client.py top250                        # Movie Top 250
    python douban_client.py now-playing                   # Now playing movies
    python douban_client.py movie-comments <subject_id>   # Movie short comments
    python douban_client.py book-comments <subject_id>    # Book short comments
    python douban_client.py reviews <movie/book> <id>     # Full reviews
    python douban_client.py user <user_id>                # User profile
    python douban_client.py import-cookies                # Import cookies from browser

Cookies: Reads from ~/.openclaw/skills/douban/cookies.json (JSON format).
Some features require login cookies.
"""

import sys
import os
import json
import re
import html as html_module
import hashlib
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_FILE = os.path.join(SKILL_DIR, "cookies.json")

HEADERS_DESKTOP = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.douban.com/",
}

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ── Cookie Management ───────────────────────────────────────────────────────

_opener = None


def get_opener():
    """Get a URL opener with cookies loaded."""
    global _opener
    if _opener is not None:
        return _opener

    cj = http.cookiejar.CookieJar()

    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE) as f:
                cookies_data = json.load(f)

            for c in cookies_data:
                domain = c.get("domain", "")
                if "douban" not in domain:
                    continue
                cookie = http.cookiejar.Cookie(
                    version=0,
                    name=c.get("name", ""),
                    value=c.get("value", ""),
                    port=None,
                    port_specified=False,
                    domain=domain,
                    domain_specified=True,
                    domain_initial_dot=domain.startswith("."),
                    path=c.get("path", "/"),
                    path_specified=True,
                    secure=c.get("secure", False),
                    expires=int(c.get("expirationDate", 0) or 0),
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={"HttpOnly": str(c.get("httpOnly", False))},
                )
                cj.set_cookie(cookie)
        except Exception as e:
            print(f"警告: 加载 cookies 失败: {e}", file=sys.stderr)

    _opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return _opener


def _solve_pow(challenge, difficulty=4):
    """Solve douban's proof-of-work challenge (SHA-512 with leading zeros)."""
    target = "0" * difficulty
    nonce = 0
    while True:
        nonce += 1
        h = hashlib.sha512((challenge + str(nonce)).encode()).hexdigest()
        if h[:difficulty] == target:
            return nonce


def _handle_pow_challenge(body, url):
    """Detect and solve douban's PoW anti-bot challenge."""
    tok_m = re.search(r'id="tok"[^>]*value="([^"]*)"', body)
    cha_m = re.search(r'id="cha"[^>]*value="([^"]*)"', body)
    if not tok_m or not cha_m:
        return body

    tok = tok_m.group(1)
    cha = cha_m.group(1)
    red_m = re.search(r'id="red"[^>]*value="([^"]*)"', body)
    redirect_url = red_m.group(1) if red_m else url

    sol = _solve_pow(cha)

    parsed = urllib.parse.urlparse(url)
    post_url = f"{parsed.scheme}://{parsed.netloc}/c"

    data = urllib.parse.urlencode({
        "tok": tok, "cha": cha, "sol": str(sol), "red": redirect_url,
    }).encode()

    hdrs = dict(HEADERS_DESKTOP)
    hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    hdrs["Referer"] = url
    req = urllib.request.Request(post_url, data=data, headers=hdrs)

    opener = get_opener()
    try:
        opener.open(req, timeout=15)
    except urllib.error.HTTPError:
        pass

    # Re-fetch original URL with the newly set cookie
    req2 = urllib.request.Request(redirect_url, headers=HEADERS_DESKTOP)
    try:
        with opener.open(req2, timeout=15) as resp2:
            return resp2.read().decode("utf-8", errors="replace")
    except Exception:
        return body


def fetch(url, headers=None, mobile=False):
    """Fetch a URL and return the response body as string."""
    hdrs = dict(HEADERS_MOBILE if mobile else HEADERS_DESKTOP)
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        opener = get_opener()
        with opener.open(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        # Handle PoW challenge (desktop only)
        if not mobile and 'id="tok"' in body and 'id="cha"' in body:
            body = _handle_pow_challenge(body, url)
        return body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        code = e.code
        if code == 403:
            return json.dumps({"error": "被豆瓣限制访问 (403)。可能需要登录 Cookie 或稍后再试。"})
        if code == 404:
            return json.dumps({"error": "页面不存在 (404)"})
        return json.dumps({"error": f"HTTP {code}: {body}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def fetch_json(url, headers=None):
    """Fetch a URL expecting JSON response."""
    hdrs = dict(HEADERS_DESKTOP)
    hdrs["Accept"] = "application/json"
    if headers:
        hdrs.update(headers)
    body = fetch(url, headers=hdrs)
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"error": "非 JSON 响应", "body": body[:500]}


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_module.unescape(text)
    return text.strip()


def truncate(text, length=200):
    text = text.replace("\n", " ")
    if len(text) > length:
        return text[:length] + "..."
    return text


def check_error(r):
    if isinstance(r, dict) and "error" in r:
        print(f"错误: {r['error']}")
        return True
    return False


# ── Import Cookies ──────────────────────────────────────────────────────────

def cmd_import_cookies():
    """Guide user to import cookies."""
    print("=== 导入豆瓣 Cookies ===\n")
    print("方法 1: 使用浏览器扩展 (推荐)")
    print("  1. 安装 'Cookie-Editor' 或 'EditThisCookie' 浏览器扩展")
    print("  2. 登录 douban.com")
    print("  3. 点击扩展图标 → Export (JSON 格式)")
    print(f"  4. 将导出的 JSON 保存到: {COOKIE_FILE}")
    print()
    print("JSON 格式示例:")
    print('[{"name": "dbcl2", "value": "...", "domain": ".douban.com", "path": "/"}]')
    print()
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE) as f:
                data = json.load(f)
            douban = [c for c in data if "douban" in c.get("domain", "")]
            print(f"当前状态: cookies.json 已存在，含 {len(douban)} 个豆瓣 cookie")
            key_cookies = [c["name"] for c in douban if c["name"] in ("dbcl2", "ck", "bid")]
            if key_cookies:
                print(f"  关键 cookie: {', '.join(key_cookies)}")
            if "dbcl2" not in key_cookies:
                print("  ⚠ 缺少 dbcl2 (登录 token)，部分功能将不可用")
        except Exception as e:
            print(f"当前状态: cookies.json 存在但读取失败: {e}")
    else:
        print(f"当前状态: cookies.json 不存在")


# ── Search via DuckDuckGo ───────────────────────────────────────────────────

def _search_duckduckgo(keyword, site_filter="douban.com"):
    """Search douban content via DuckDuckGo."""
    query = urllib.parse.quote(f"{keyword} site:{site_filter}")
    url = f"https://html.duckduckgo.com/html/?q={query}"
    req = urllib.request.Request(url, headers={
        "User-Agent": HEADERS_DESKTOP["User-Agent"],
        "Accept": "text/html",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

    results = re.findall(
        r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>',
        page,
    )
    snippets = re.findall(
        r'<a class="result__snippet"[^>]*>(.*?)</a>',
        page,
        re.DOTALL,
    )

    items = []
    for i, (raw_link, raw_title) in enumerate(results):
        title = strip_html(raw_title)
        snippet = strip_html(snippets[i]) if i < len(snippets) else ""

        m = re.search(r'uddg=([^&]+)', raw_link)
        link = urllib.parse.unquote(m.group(1)) if m else raw_link

        if "douban.com" not in link:
            continue

        items.append({"title": title, "snippet": snippet, "link": link})
        if len(items) >= 15:
            break

    return items


def _classify_douban_url(link):
    """Classify a douban URL by type."""
    if "/subject/" in link:
        if "movie.douban.com" in link:
            return "电影"
        elif "book.douban.com" in link:
            return "图书"
        elif "music.douban.com" in link:
            return "音乐"
        return "条目"
    elif "/group/" in link:
        return "小组"
    elif "/people/" in link:
        return "用户"
    elif "/review/" in link:
        return "评论"
    return "豆瓣"


def cmd_search(keyword):
    items = _search_duckduckgo(keyword)
    if not items:
        print("未找到相关结果，请尝试其他关键词")
        return

    print(f"搜索「{keyword}」结果:\n")
    for i, item in enumerate(items, 1):
        tag = _classify_douban_url(item["link"])
        sid_m = re.search(r'/subject/(\d+)', item["link"])
        print(f"{i}. [{tag}] {item['title']}")
        if item["snippet"]:
            print(f"   {truncate(item['snippet'], 150)}")
        print(f"   {item['link']}")
        if sid_m:
            print(f"   ID: {sid_m.group(1)}")
        print()


def cmd_search_movie(keyword):
    # Try suggest API first for exact matches
    suggest_url = f"https://movie.douban.com/j/subject_suggest?q={urllib.parse.quote(keyword)}"
    r = fetch_json(suggest_url)
    if isinstance(r, list) and r:
        print(f"搜索电影「{keyword}」结果:\n")
        for i, item in enumerate(r, 1):
            title = item.get("title", "")
            year = item.get("year", "")
            sub_title = item.get("sub_title", "")
            sid = item.get("id", "")
            year_str = f" ({year})" if year else ""
            sub_str = f" / {sub_title}" if sub_title else ""
            print(f"{i}. {title}{year_str}{sub_str}")
            print(f"   https://movie.douban.com/subject/{sid}/")
            print(f"   ID: {sid}")
            print()
        if len(r) < 5:
            print("提示: 以上为精确匹配，如需更多结果可使用 search 命令\n")
        return

    # Fallback to DuckDuckGo
    items = _search_duckduckgo(keyword, "movie.douban.com")
    if not items:
        print("未找到相关电影结果")
        return

    print(f"搜索电影「{keyword}」结果:\n")
    for i, item in enumerate(items, 1):
        sid_m = re.search(r'/subject/(\d+)', item["link"])
        print(f"{i}. {item['title']}")
        if item["snippet"]:
            print(f"   {truncate(item['snippet'], 150)}")
        print(f"   {item['link']}")
        if sid_m:
            print(f"   ID: {sid_m.group(1)}")
        print()


def cmd_search_book(keyword):
    suggest_url = f"https://book.douban.com/j/subject_suggest?q={urllib.parse.quote(keyword)}"
    r = fetch_json(suggest_url)
    if isinstance(r, list) and r:
        print(f"搜索图书「{keyword}」结果:\n")
        for i, item in enumerate(r, 1):
            title = item.get("title", "")
            sub_title = item.get("sub_title", "")
            sid = item.get("id", "")
            sub_str = f" / {sub_title}" if sub_title else ""
            print(f"{i}. {title}{sub_str}")
            print(f"   https://book.douban.com/subject/{sid}/")
            print(f"   ID: {sid}")
            print()
        return

    items = _search_duckduckgo(keyword, "book.douban.com")
    if not items:
        print("未找到相关图书结果")
        return

    print(f"搜索图书「{keyword}」结果:\n")
    for i, item in enumerate(items, 1):
        sid_m = re.search(r'/subject/(\d+)', item["link"])
        print(f"{i}. {item['title']}")
        if item["snippet"]:
            print(f"   {truncate(item['snippet'], 150)}")
        print(f"   {item['link']}")
        if sid_m:
            print(f"   ID: {sid_m.group(1)}")
        print()


def cmd_search_music(keyword):
    items = _search_duckduckgo(keyword, "music.douban.com")
    if not items:
        print("未找到相关音乐结果")
        return

    print(f"搜索音乐「{keyword}」结果:\n")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['title']}")
        if item["snippet"]:
            print(f"   {truncate(item['snippet'], 150)}")
        print(f"   {item['link']}")
        print()


def cmd_search_group(keyword):
    items = _search_duckduckgo(keyword + " 豆瓣小组", "douban.com/group")
    if not items:
        print("未找到相关小组结果")
        return

    print(f"搜索小组「{keyword}」结果:\n")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['title']}")
        if item["snippet"]:
            print(f"   {truncate(item['snippet'], 150)}")
        print(f"   {item['link']}")
        print()


# ── Movie Detail (via mobile site) ─────────────────────────────────────────

def cmd_movie(subject_id):
    url = f"https://m.douban.com/movie/subject/{subject_id}/"
    body = fetch(url, mobile=True)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    # Title from <title> tag
    title_m = re.search(r'<title>\s*(.*?)\s*</title>', body, re.DOTALL)
    title = title_m.group(1).strip().replace(" - 电影\n - 豆瓣", "").replace(" - 电影 - 豆瓣", "").strip() if title_m else ""

    # Rating & count from meta tags
    rating_m = re.search(r'itemprop="ratingValue" content="([\d.]+)"', body)
    rating = rating_m.group(1) if rating_m else "暂无"
    count_m = re.search(r'itemprop="reviewCount" content="(\d+)"', body)
    count = count_m.group(1) if count_m else ""

    # Meta info (country / genre / date / duration)
    meta_m = re.search(r'<div class="sub-meta">(.*?)</div>', body, re.DOTALL)
    meta = strip_html(meta_m.group(1)).strip() if meta_m else ""

    # Summary from description meta tag
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', body)
    desc = ""
    if desc_m:
        desc = desc_m.group(1)
        # Remove the prefix "TITLE豆瓣评分：X.X 简介："
        desc = re.sub(r'^.*?简介：', '', desc)

    # Also try to get full intro from page body
    intro_m = re.search(r'class="bd"[^>]*>(.*?)</div>', body, re.DOTALL)
    if intro_m:
        full_intro = strip_html(intro_m.group(1))
        if len(full_intro) > len(desc):
            desc = full_intro

    print(f"{title}")
    count_str = f" ({count}人评价)" if count else ""
    print(f"评分: {rating}{count_str}")
    if meta:
        print(f"{meta}")
    if desc:
        print(f"\n剧情简介:\n{desc}")
    print(f"\nhttps://movie.douban.com/subject/{subject_id}/")


# ── Book Detail (via mobile site) ──────────────────────────────────────────

def cmd_book(subject_id):
    url = f"https://m.douban.com/book/subject/{subject_id}/"
    body = fetch(url, mobile=True)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    # Title
    title_m = re.search(r'<title>\s*(.*?)\s*</title>', body, re.DOTALL)
    raw_title = title_m.group(1).strip() if title_m else ""
    title = re.sub(r'\s*-\s*(图书|书籍)?\s*-?\s*豆瓣\s*$', '', raw_title).strip()

    # Rating
    rating_m = re.search(r'itemprop="ratingValue" content="([\d.]+)"', body)
    rating = rating_m.group(1) if rating_m else "暂无"
    count_m = re.search(r'itemprop="reviewCount" content="(\d+)"', body)
    count = count_m.group(1) if count_m else ""

    # Meta info
    meta_m = re.search(r'<div class="sub-meta">(.*?)</div>', body, re.DOTALL)
    meta = strip_html(meta_m.group(1)).strip() if meta_m else ""

    # Description
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', body)
    desc = ""
    if desc_m:
        desc = desc_m.group(1)
        desc = re.sub(r'^.*?简介：', '', desc)

    intro_m = re.search(r'class="bd"[^>]*>(.*?)</div>', body, re.DOTALL)
    if intro_m:
        full_intro = strip_html(intro_m.group(1))
        if len(full_intro) > len(desc):
            desc = full_intro

    print(f"{title}")
    count_str = f" ({count}人评价)" if count else ""
    print(f"评分: {rating}{count_str}")
    if meta:
        print(f"{meta}")
    if desc:
        print(f"\n内容简介:\n{desc}")
    print(f"\nhttps://book.douban.com/subject/{subject_id}/")


# ── Top 250 ─────────────────────────────────────────────────────────────────

def cmd_top250():
    url = "https://movie.douban.com/top250"
    body = fetch(url)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    # Extract each movie item block individually
    item_blocks = re.findall(r'<div class="item">(.*?)</div>\s*</div>\s*</div>', body, re.DOTALL)

    if not item_blocks:
        print("获取 Top250 失败（可能被限流，请稍后再试）")
        return

    print("豆瓣电影 Top 250:\n")
    for i, block in enumerate(item_blocks, 1):
        sid_m = re.search(r'href="https://movie\.douban\.com/subject/(\d+)/"', block)
        sid = sid_m.group(1) if sid_m else ""
        title_m = re.search(r'<span class="title">([^<]+)</span>', block)
        title = title_m.group(1) if title_m else "未知"
        rating_m = re.search(r'<span class="rating_num"[^>]*>([\d.]+)</span>', block)
        rating = rating_m.group(1) if rating_m else "暂无"
        count_m = re.search(r'<span>(\d+)人评价</span>', block)
        count = count_m.group(1) if count_m else ""
        quote_m = re.search(r'<span class="inq">([^<]*)</span>', block)
        quote = quote_m.group(1) if quote_m else ""

        count_str = f" ({count}人评价)" if count else ""
        line = f"{i}. {title}  评分: {rating}{count_str}"
        if quote:
            line += f"\n   「{quote}」"
        if sid:
            line += f"\n   https://movie.douban.com/subject/{sid}/"
        print(line)
        print()


# ── Now Playing ─────────────────────────────────────────────────────────────

def cmd_now_playing():
    url = "https://movie.douban.com/cinema/nowplaying/"
    body = fetch(url)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    items = re.findall(
        r'<li[^>]*id="(\d+)"[^>]*data-title="([^"]*)"[^>]*data-score="([^"]*)"'
        r'[^>]*data-star="([^"]*)"[^>]*data-release="([^"]*)"[^>]*data-duration="([^"]*)"'
        r'[^>]*data-region="([^"]*)"[^>]*data-director="([^"]*)"[^>]*data-actors="([^"]*)"',
        body,
    )

    if not items:
        print("获取正在热映列表失败（可能被限流，请稍后再试）")
        return

    print("正在热映:\n")
    for i, (sid, title, score, star, release, duration, region, director, actors) in enumerate(items, 1):
        score_str = f"  评分: {score}" if score else ""
        print(f"{i}. {title}{score_str}")
        info_parts = []
        if director:
            info_parts.append(f"导演: {director}")
        if actors:
            info_parts.append(f"主演: {actors}")
        if info_parts:
            print(f"   {' / '.join(info_parts)}")
        meta_parts = []
        if release:
            meta_parts.append(f"上映: {release}")
        if duration:
            meta_parts.append(f"片长: {duration}")
        if region:
            meta_parts.append(f"地区: {region}")
        if meta_parts:
            print(f"   {' / '.join(meta_parts)}")
        print(f"   https://movie.douban.com/subject/{sid}/")
        print()


# ── Movie Comments ──────────────────────────────────────────────────────────

def cmd_movie_comments(subject_id):
    url = f"https://movie.douban.com/subject/{subject_id}/comments?status=P&sort=new_score"
    body = fetch(url)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    comments = re.findall(
        r'<span class="comment-info">.*?<a href="[^"]*"[^>]*>([^<]+)</a>.*?'
        r'(?:<span class="allstar(\d)0 rating")?.*?'
        r'<span class="comment-time\s*"[^>]*title="([^"]*)"[^>]*>.*?'
        r'<span class="short">([^<]+)</span>.*?'
        r'<span class="vote-count">(\d*)</span>',
        body,
        re.DOTALL,
    )

    if not comments:
        print("暂无短评或获取失败（可能需要登录 Cookie）")
        return

    title_m = re.search(r'<title>([^<]+)</title>', body)
    title = strip_html(title_m.group(1)).replace("的短评", "").strip() if title_m else ""

    if title:
        print(f"{title} 短评:\n")
    else:
        print("短评:\n")

    for i, (user, star, date, content, votes) in enumerate(comments, 1):
        star_str = f" {'★' * int(star)}{'☆' * (5 - int(star))}" if star else ""
        votes_str = f"  ({votes}有用)" if votes and votes != "0" else ""
        print(f"{i}. [{user}]{star_str}{votes_str}")
        print(f"   {content.strip()}")
        if date:
            print(f"   {date.strip()}")
        print()


# ── Book Comments ───────────────────────────────────────────────────────────

def cmd_book_comments(subject_id):
    url = f"https://book.douban.com/subject/{subject_id}/comments/?status=P&sort=new_score"
    body = fetch(url)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    comments = re.findall(
        r'<span class="comment-info">.*?<a href="[^"]*"[^>]*>([^<]+)</a>.*?'
        r'(?:<span class="user-stars allstar(\d)0 rating")?.*?'
        r'<span class="comment-time">([^<]*)</span>.*?'
        r'<p class="comment-content">\s*<span class="short">([^<]+)</span>.*?'
        r'<span class="vote-count">(\d*)</span>',
        body,
        re.DOTALL,
    )

    if not comments:
        print("暂无短评或获取失败（可能需要登录 Cookie）")
        return

    title_m = re.search(r'<title>([^<]+)</title>', body)
    title = strip_html(title_m.group(1)).replace("的短评", "").strip() if title_m else ""

    if title:
        print(f"{title} 短评:\n")
    else:
        print("短评:\n")

    for i, (user, star, date, content, votes) in enumerate(comments, 1):
        star_str = f" {'★' * int(star)}{'☆' * (5 - int(star))}" if star else ""
        votes_str = f"  ({votes}有用)" if votes and votes != "0" else ""
        print(f"{i}. [{user}]{star_str}{votes_str}")
        print(f"   {content.strip()}")
        if date.strip():
            print(f"   {date.strip()}")
        print()


# ── Reviews ─────────────────────────────────────────────────────────────────

def cmd_reviews(cat, subject_id):
    if cat not in ("movie", "book"):
        print("类型必须是 movie 或 book")
        return

    # Use mobile site to avoid PoW
    url = f"https://m.douban.com/{cat}/subject/{subject_id}/reviews"
    body = fetch(url, mobile=True)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    # Mobile page structure: <a href="/movie/review/ID"><h3>Title</h3>...<div class="info">N 有用</div></a>
    review_blocks = re.findall(
        r'<a href="/' + cat + r'/review/(\d+)[^"]*">\s*<h3>(.*?)</h3>.*?(\d+)\s*有用',
        body,
        re.DOTALL,
    )

    if not review_blocks:
        # Fallback: just find review IDs
        review_links = re.findall(r'/' + cat + r'/review/(\d+)', body)
        seen = set()
        unique_ids = []
        for rid in review_links:
            if rid not in seen:
                seen.add(rid)
                unique_ids.append(rid)
        if not unique_ids:
            print("暂无评论或获取失败")
            return
        cat_label = "影评" if cat == "movie" else "书评"
        base_url = f"https://{cat}.douban.com"
        print(f"{cat_label}:\n")
        for i, rid in enumerate(unique_ids[:15], 1):
            print(f"{i}. {base_url}/review/{rid}/")
            print()
        return

    # Deduplicate by ID
    seen = set()
    unique = []
    for rid, raw_title, useful in review_blocks:
        if rid not in seen:
            seen.add(rid)
            unique.append((rid, strip_html(raw_title).strip(), useful))

    cat_label = "影评" if cat == "movie" else "书评"
    base_url = f"https://{cat}.douban.com"
    print(f"{cat_label}:\n")
    for i, (rid, title, useful) in enumerate(unique[:15], 1):
        useful_str = f"  ({useful}有用)" if useful and useful != "0" else ""
        print(f"{i}. {title}{useful_str}")
        print(f"   {base_url}/review/{rid}/")
        print()


# ── User Profile ────────────────────────────────────────────────────────────

def cmd_user(user_id):
    url = f"https://www.douban.com/people/{user_id}/"
    body = fetch(url)

    if body.startswith("{"):
        r = json.loads(body)
        if check_error(r):
            return

    # Name
    name_m = re.search(r'<title>([^<]+)</title>', body)
    name = strip_html(name_m.group(1)).strip() if name_m else user_id

    # Info
    info_m = re.search(r'<div class="user-info">(.*?)</div>', body, re.DOTALL)
    info = strip_html(info_m.group(1)).strip() if info_m else ""

    # Signature / intro
    sig_m = re.search(r'<span id="intro_display">(.*?)</span>', body, re.DOTALL)
    sig = strip_html(sig_m.group(1)).strip() if sig_m else ""

    print(f"{name}")
    if info:
        print(f"  {info}")
    if sig:
        print(f"  简介: {sig}")
    print(f"  https://www.douban.com/people/{user_id}/")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "search": (cmd_search, 1),
        "search-movie": (cmd_search_movie, 1),
        "search-book": (cmd_search_book, 1),
        "search-music": (cmd_search_music, 1),
        "search-group": (cmd_search_group, 1),
        "movie": (cmd_movie, 1),
        "book": (cmd_book, 1),
        "top250": (cmd_top250, 0),
        "now-playing": (cmd_now_playing, 0),
        "movie-comments": (cmd_movie_comments, 1),
        "book-comments": (cmd_book_comments, 1),
        "reviews": (cmd_reviews, 2),
        "user": (cmd_user, 1),
        "import-cookies": (cmd_import_cookies, 0),
    }

    if cmd not in commands:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

    func, nargs = commands[cmd]
    if len(args) < nargs:
        print(f"命令 '{cmd}' 需要 {nargs} 个参数")
        sys.exit(1)

    func(*args[:nargs])


if __name__ == "__main__":
    main()
