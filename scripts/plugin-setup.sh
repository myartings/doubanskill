#!/usr/bin/env bash
# Claude Code 插件初始化脚本（不影响 OpenClaw 安装）
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SKILL_NAME="douban"
LINK_PATH="$HOME/.openclaw/skills/$SKILL_NAME"

echo "=== 豆瓣 Skill 插件初始化 ==="

# 创建 ~/.openclaw/skills/douban 软链接，使 SKILL.md 中的路径可用
if [ ! -e "$LINK_PATH" ]; then
    mkdir -p "$(dirname "$LINK_PATH")"
    ln -s "$SKILL_DIR" "$LINK_PATH"
    echo "创建软链接: $LINK_PATH -> $SKILL_DIR"
else
    echo "$LINK_PATH 已存在，跳过"
fi

# 调用原始 setup.sh
bash "$SCRIPT_DIR/setup.sh"
