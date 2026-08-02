#!/usr/bin/env python3
"""Restructure the authoritative Master GDD into a clean part/chapter hierarchy.

The migration is intentionally idempotent. It does not delete, summarize, or
rewrite design content. It only:

1. groups the document into seven professional parts;
2. demotes existing chapters and subsections by one heading level;
3. keeps the existing numeric chapter IDs for compatibility;
4. replaces the mixed quick-navigation block with a concise part index;
5. updates the concept version to v0.4.2.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs/design/00-master-game-concept.md"
MARKER = "<!-- MASTER_GDD_STRUCTURE_V0_4_2 -->"

PART_0 = "PART 0｜文档导读与总览"
PART_1 = "PART I｜游戏愿景与世界框架"
PART_2 = "PART II｜核心循环、成长与操控"
PART_3 = "PART III｜生态、事件与角色存续"
PART_4 = "PART IV｜联机、经济与空间战斗"
PART_5 = "PART V｜首个可玩原型"
PART_6 = "PART VI｜决策记录与项目治理"


def part_for_chapter(number: int) -> str:
    if 0 <= number <= 5:
        return PART_1
    if 6 <= number <= 12:
        return PART_2
    if 13 <= number <= 17:
        return PART_3
    if 18 <= number <= 24:
        return PART_4
    if number == 25:
        return PART_5
    return PART_6


def replace_navigation(text: str) -> str:
    navigation = r'''### 分卷目录

主目录只保留“分卷—章节”两级。章内小节继续保留在正文中，但不再挤入主目录；旧章节编号不变，历史引用仍然有效。

| 分卷 | 主要内容 | 快速入口 |
|---|---|---|
| PART 0 | 文档控制、状态图例、一页式全貌、系统状态和产品边界 | [进入](#part-0-文档导读与总览) |
| PART I | 产品定位、核心体验、世界、场景和镜头 | [进入](#part-i-游戏愿景与世界框架) |
| PART II | 农业日、持久成长、卡牌变异、玩家、宠物和机械单位 | [进入](#part-ii-核心循环成长与操控) |
| PART III | 敌对生态、奶牛、风险委托、天气灾害和复生 | [进入](#part-iii-生态事件与角色存续) |
| PART IV | 单机合作、PvPvE、离线保护、经济、路径和多人缩放 | [进入](#part-iv-联机经济与空间战斗) |
| PART V | 第一阶段可玩原型、明确不做和验收条件 | [进入](#part-v-首个可玩原型) |
| PART VI | 待定事项、决策总表、弃用记录、维护规则和非目标 | [进入](#part-vi-决策记录与项目治理) |

#### 目录维护规则

- **主目录层级**：只显示分卷与章节；
- **章内结构**：系统机制、流程、边界、例外和数值假设放在章内小节；
- **状态归属**：待定、待验证和弃用内容既保留在所属系统章节，也进入PART VI集中索引；
- **编号稳定性**：原有0—31章编号继续保留，后续优先在现有章节内增量修订；
- **新增章节**：只有出现无法归入现有系统的新领域时才新增，不因一次讨论随意拆章。'''

    pattern = re.compile(
        r"### 快速导航\n\n.*?(?=\n## 一页式游戏全貌)",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise RuntimeError("Cannot find the existing quick-navigation block")
    return pattern.sub(navigation, text, count=1)


def restructure_headings(text: str) -> str:
    # Give the four introductory chapters stable, readable names before the
    # generic heading transformation.
    replacements = {
        "## GDD阅读入口": "## A.1 文档控制与阅读说明",
        "## 一页式游戏全貌": "## A.2 一页式游戏全貌",
        "## 系统状态总览": "## A.3 系统状态总览",
        "## 当前产品边界": "## A.4 当前产品边界",
    }
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"Cannot find introductory chapter: {old}")
        text = text.replace(old, new, 1)

    output: list[str] = []
    current_part: str | None = None
    seen_numbered_chapter = False
    in_fenced_code = False

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fenced_code = not in_fenced_code
            output.append(line)
            continue

        if not in_fenced_code:
            match = re.match(r"^(#{2,5})\s+(.+)$", line)
            if match:
                marks, title = match.groups()
                level = len(marks)

                if level == 2:
                    number_match = re.match(r"(\d+)\.", title)
                    if number_match:
                        seen_numbered_chapter = True
                        target_part = part_for_chapter(int(number_match.group(1)))
                    elif not seen_numbered_chapter:
                        target_part = PART_0
                    else:
                        # Any legacy unnumbered top-level chapter remains in
                        # the surrounding part instead of creating a stray
                        # top-level item.
                        target_part = current_part or PART_6

                    if target_part != current_part:
                        if output and output[-1] != "":
                            output.append("")
                        output.append(f"## {target_part}")
                        output.append("")
                        current_part = target_part

                    output.append(f"### {title}")
                    continue

                # Existing chapter internals move down one level so that the
                # HTML TOC, which reads H2/H3, shows only parts and chapters.
                output.append(f"{'#' * min(level + 1, 6)} {title}")
                continue

        output.append(line)

    return "\n".join(output).rstrip() + "\n"


def update_version(text: str) -> str:
    text = text.replace("版本：Concept v0.4.1", "版本：Concept v0.4.2", 1)
    text = text.replace("更新时间：2026-08-01", "更新时间：2026-08-02", 1)
    text = text.replace("**当前概念版本**：Concept v0.4.1", "**当前概念版本**：Concept v0.4.2", 1)

    if MARKER not in text:
        authority = "> 本文是项目当前唯一权威的主游戏设计文档"
        index = text.find(authority)
        if index < 0:
            raise RuntimeError("Cannot find Master GDD authority statement")
        text = text[:index] + MARKER + "\n\n" + text[index:]
    return text


def update_governance_version() -> None:
    for relative in ("README.md", "VERSIONING.md", "AGENTS.md"):
        path = ROOT / relative
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        updated = content.replace("Concept v0.4.1", "Concept v0.4.2")
        if updated != content:
            path.write_text(updated.rstrip() + "\n", encoding="utf-8", newline="\n")

    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        content = changelog.read_text(encoding="utf-8")
        heading = "## Concept v0.4.2 — Master GDD目录结构重构"
        if heading not in content:
            entry = f'''{heading}

- 将主游戏设计改为PART 0—PART VI的分卷结构；
- 主目录仅显示“分卷—章节”两级，章内小节不再混入主目录；
- 保留原有0—31章编号、全部设计内容和历史引用；
- 将待定、待验证、弃用与治理记录集中置于PART VI。

'''
            first_release = content.find("## ")
            if first_release >= 0:
                content = content[:first_release] + entry + content[first_release:]
            else:
                content = content.rstrip() + "\n\n" + entry
            changelog.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    text = MASTER.read_text(encoding="utf-8")
    if MARKER in text:
        update_governance_version()
        return

    text = replace_navigation(text)
    text = restructure_headings(text)
    text = update_version(text)
    MASTER.write_text(text, encoding="utf-8", newline="\n")
    update_governance_version()


if __name__ == "__main__":
    main()
