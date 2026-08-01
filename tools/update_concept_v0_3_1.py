#!/usr/bin/env python3
"""Apply the Concept v0.3.1 incremental documentation migration.

This script is intentionally idempotent. It only inserts or replaces the exact
sections introduced by the related discussion and leaves unrelated content and
file layout untouched.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Cannot find replacement anchor: {label}")
    return text.replace(old, new, 1)


def insert_after_once(text: str, anchor: str, addition: str, marker: str) -> str:
    if marker in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Cannot find insertion anchor for: {marker}")
    return text.replace(anchor, anchor + addition, 1)


def update_master() -> None:
    rel = "docs/design/00-master-game-concept.md"
    text = read(rel)
    text = replace_once(
        text,
        "# 《PvZ Infinite / 植物大战僵尸：无限》主游戏构思",
        "# 《PvZ Infinite / 植物大战僵尸：无限 / 农场：无限（名称待定）》主游戏构思",
        "master title",
    )
    text = replace_once(text, "版本：Concept v0.3.0", "版本：Concept v0.3.1", "master version")

    name_section = """

## 0. 名称状态与候选方案

项目正式名称尚未确定。当前候选包括：

1. **PvZ Infinite / 植物大战僵尸：无限**：当前内部概念代号，识别度高，但公开发行和商业化存在明显知识产权风险；
2. **农场：无限 / Farm: Infinite**：新增候选，更贴合“永久农场 + 无限成长 + 多威胁防御”的原创定位，可作为当前优先研究方向；
3. **其他原创名称**：后续结合世界观、角色、美术与市场定位继续征集和筛选。

在正式定名前，仓库名 `PvZ-Infinite` 保持不变，避免历史链接失效；文档中同时保留内部代号和原创候选。
"""
    text = insert_after_once(
        text,
        "> 本文是当前游戏构思的完整主索引。它不替代历史讨论记录，也不删除旧版本细节。后续迭代必须采用增量修改：只调整新讨论涉及的章节，并在变更日志中记录原因、影响范围和保留内容。",
        name_section,
        "## 0. 名称状态与候选方案",
    )

    text = insert_after_once(
        text,
        "- “对门”可以存在于十字路口或道路两侧，但现实距离在游戏中适当压缩。",
        "\n\n> **弃用想法：城市住宅式密集街区作为主要农场布局。** 该方案会削弱美国大型农场的空间感与真实性。保留“邻居/对门”的社交关系，但改用县道邻居、乡村十字路口、家族农场或农业合作社布局。",
        "弃用想法：城市住宅式密集街区",
    )
    text = insert_after_once(
        text,
        "白天可以视为“安全程度较高的局外层”，但仍属于同一个连续世界。小规模事件、远征和突发袭击仍可发生。",
        "\n\n> **弃用想法：把“无限”设计成一场完全没有昼夜结算、喘息和阶段边界的永不结束战斗。** 该方案容易导致数值失控、下线焦虑和联机同步困难。当前采用永久世界不结束，但每个农业日有明确阶段与黎明结算。",
        "弃用想法：把“无限”设计成一场完全没有昼夜结算",
    )
    text = insert_after_once(
        text,
        "- 农场及区域势力关系。",
        "\n\n> **弃用想法：每到黎明统一重置植物变异、炮塔和全部天气效果。** 当前仅重置肉鸽卡牌、短期天气、临时命令与当夜规则；存活植物、持久变异、炮塔和长期灾害继续存在，只有被摧毁、主动拆解、失控或剧情事件才会损失。",
        "弃用想法：每到黎明统一重置植物变异",
    )
    text = insert_after_once(
        text,
        "- 同时保留WASD模式，避免鼠标跟随长时间使用造成疲劳。",
        "\n\n> **弃用想法：把玩家存在方式限定为互斥的三选一——纯策略指挥、纯自由角色，或只在危机时临时接管角色/机甲。** 当前方案是策略指挥与自由主体始终融合：普通植物和设施自动工作，玩家角色持续在场，大型无人设备使用简化区域命令。",
        "弃用想法：把玩家存在方式限定为互斥的三选一",
    )
    text = insert_after_once(
        text,
        "原“风险契约”更名建议为“风险委托”。它是玩家主动接受额外困难以换取稀有奖励的可选条件，不是强制重置规则。",
        "\n\n> **弃用名称：“风险契约”。** 该名称容易让人误解为长期绑定或系统强制条款。当前采用“风险委托”，但旧名称仍保留用于追溯早期讨论。",
        "弃用名称：“风险契约”",
    )
    text = insert_after_once(
        text,
        "灵感来自《瑞克和莫蒂》Operation Phoenix，但正式项目使用原创设定和名称。当前推荐“火种计划”。",
        "\n\n> **弃用名称与直接引用：正式系统使用“凤凰计划”或 Operation Phoenix。** 它仅作为灵感来源和内部讨论标签；正式世界观使用原创名称与机制，当前推荐“火种计划”。",
        "弃用名称与直接引用：正式系统使用“凤凰计划”",
    )
    text = insert_after_once(
        text,
        "原家园资产不复制，防止反复切换模式刷资源。",
        "\n\n> **弃用想法：加入玩家把原单机世界的全部资源、属性和建筑压缩叠加到合作世界的一栋房屋上。** 该方案会制造超级建筑、资源复制和主客不公平。当前改用迁入额度、蓝图继承、预制模块和家园价值补给。",
        "弃用想法：加入玩家把原单机世界的全部资源",
    )
    text = insert_after_once(
        text,
        "永久家园不作为可被一次匹配彻底删除的对象。玩家携带有限资源进入战区，建立战地基地或前哨站。",
        "\n\n> **弃用想法：自由对抗直接加载玩家的完整永久农场，并允许一次匹配永久摧毁除大本营外的大量长期设施。** 该方案会让失败成本过高并鼓励离线规避。当前采用永久家园与战斗实例分离，真实损失集中在带入资源、战地设施和未撤离战利品。",
        "弃用想法：自由对抗直接加载玩家的完整永久农场",
    )
    text = insert_after_once(
        text,
        "高能储能可通过游戏内生产、战斗、掠夺和其他系统获得。商业化时不建议直接出售无限战力能源，避免付费优势破坏公平。",
        "\n\n> **弃用想法：通过充值直接购买可无限累积、显著提高离线杀敌和掉落效率的高能护罩能源。** 该方案会形成明显的付费战力与离线资源优势。付费内容优先考虑外观、主题和非战力便利。",
        "弃用想法：通过充值直接购买可无限累积",
    )
    text = replace_once(
        text,
        "- 被否定的旧方案保留在对话记录和变更日志中；",
        "- 被否定的旧方案除保留在对话记录和变更日志外，还必须写回对应设计章节，并明确标注“弃用想法”或“弃用名称”；",
        "master maintenance deprecated rule",
    )
    write(rel, text)


def update_core_loop() -> None:
    rel = "docs/design/01-core-loop-and-modes.md"
    text = read(rel)
    anchor = "肉鸽卡牌可以在当夜诱发真正的植物突变、设施改造或驯化结果。卡牌本身在黎明失效，但当夜已经形成并存活的结果继续保留。"
    addition = "\n\n> **弃用想法：每夜统一删除植物变异、炮塔、路障和长期天气。** 当前改为选择性重置：只结束肉鸽卡牌、短期天气、临时命令和当次规则；农场资产按存活、损坏和摧毁状态延续。"
    text = insert_after_once(text, anchor, addition, "弃用想法：每夜统一删除植物变异")
    write(rel, text)


def update_persistence_doc() -> None:
    rel = "docs/design/02-persistent-growth-player-avatar-and-phoenix.md"
    text = read(rel)
    text = insert_after_once(
        text,
        "当前建议不再采用“每夜清空植物变异和炮塔”的方案。",
        "\n\n> **弃用想法：每夜清空植物变异和炮塔。** 该方案虽然易于控制数值，但破坏永久农场的历史感和玩家对独特资产的感情，因此被选择性重置与自然约束方案替代。",
        "弃用想法：每夜清空植物变异和炮塔",
    )
    text = insert_after_once(
        text,
        "本作不采用纯RTS指挥，也不采用需要频繁手动射击的动作游戏，而是两者融合。",
        "\n\n> **弃用想法：将纯策略、自由主体、危机接管设计成互斥选项。** 当前不是模式切换，而是玩家主体与轻量策略同时持续存在。",
        "弃用想法：将纯策略、自由主体、危机接管",
    )
    text = insert_after_once(
        text,
        "当前推荐中文名“火种计划”，内部仍可备注其灵感来源。",
        "\n\n> **弃用名称：正式沿用“凤凰计划”或 Operation Phoenix。** 为避免直接借用既有作品的专有表达，正式系统必须使用原创名称；旧称仅保留在灵感说明与历史记录中。",
        "弃用名称：正式沿用“凤凰计划”",
    )
    write(rel, text)


def update_readme() -> None:
    rel = "README.md"
    text = read(rel)
    text = replace_once(
        text,
        "# PvZ Infinite / 植物大战僵尸：无限（暂定名）",
        "# PvZ Infinite / 植物大战僵尸：无限 / 农场：无限（名称待定）",
        "README title",
    )
    text = replace_once(text, "Concept v0.3.0（2026-08-01）", "Concept v0.3.1（2026-08-01）", "README version")
    name_block = """

## 名称候选

- **PvZ Infinite / 植物大战僵尸：无限**：当前内部概念代号；
- **农场：无限 / Farm: Infinite**：新增原创候选，当前优先研究；
- 正式名称仍待结合世界观、美术、市场定位和知识产权评估后确定。
"""
    text = insert_after_once(
        text,
        "当前基线：**Concept v0.3.1（2026-08-01）**。",
        name_block,
        "## 名称候选",
    )
    text = insert_after_once(
        text,
        "- [当前完整主游戏构思（Concept v0.3.0）](docs/design/00-master-game-concept.md)",
        "\n- [单文件集成式项目档案（持续自动更新）](PvZ-Infinite-Archive.html)",
        "单文件集成式项目档案",
    )
    text = text.replace("当前完整主游戏构思（Concept v0.3.0）", "当前完整主游戏构思（Concept v0.3.1）", 1)
    text = insert_after_once(
        text,
        "- 被否定的旧方案仍保留在原始问答和变更日志中；",
        "\n- 被否定方案同时写入对应设计章节，并明确标注“弃用想法”或“弃用名称”；",
        "被否定方案同时写入对应设计章节",
    )
    write(rel, text)


def update_versioning() -> None:
    rel = "VERSIONING.md"
    text = read(rel)
    text = replace_once(
        text,
        "4. 旧方案被否定后，在主设计稿中更新当前结论，同时在变更日志和原始对话中保留旧方案及否定原因。",
        "4. 旧方案被否定后，在对应设计章节保留并标注“弃用想法”或“弃用名称”，同时在主设计稿更新当前结论，并在变更日志和原始对话中保留否定原因。",
        "VERSIONING deprecated rule",
    )
    text = replace_once(text, "当前版本：`Concept v0.3.0`。", "当前版本：`Concept v0.3.1`。", "VERSIONING version")
    text = insert_after_once(
        text,
        "- `VERSIONING.md`：本规则。",
        "\n- `PvZ-Infinite-Archive.html`：所有仓库内容的单文件无损快照与交互式阅读界面；\n- `tools/build_archive.py`：持续生成上述HTML快照。",
        "PvZ-Infinite-Archive.html",
    )
    write(rel, text)


def update_charter() -> None:
    rel = "docs/00-project-charter.md"
    text = read(rel)
    addition = """

## 名称状态（Concept v0.3.1增量）

正式名称待定。除内部代号“PvZ Infinite / 植物大战僵尸：无限”外，新增原创候选：**农场：无限 / Farm: Infinite**。仓库名称暂不调整，以保持历史链接与版本连续性。
"""
    if "## 名称状态（Concept v0.3.1增量）" not in text:
        text = text.rstrip() + addition + "\n"
    write(rel, text)


def update_changelog() -> None:
    rel = "CHANGELOG.md"
    text = read(rel)
    entry = """

## Concept v0.3.1 — 2026-08-01

### 新增

- 新增名称候选“农场：无限 / Farm: Infinite”，正式名称仍待定；
- 新增单文件集成式HTML项目档案及自动构建机制；
- HTML以原始字节和SHA-256保存全部仓库文件，支持阅读、搜索、原文查看、浏览器本地编辑与导出。

### 修改

- 被否定的方案不再只存在于聊天和变更日志，而是写入对应设计章节并标注“弃用想法”或“弃用名称”；
- README、主设计稿、版本规则和项目章程升级到Concept v0.3.1。

### 保持不变

- 不重构现有设计框架；
- 不删除原始聊天、讨论纪要和旧版本理由；
- 已确认的永久农场、昼夜循环、选择性重置、自由主体、简化指挥、火种计划、合作和PvPvE框架保持不变。
"""
    if "## Concept v0.3.1" not in text:
        text = text.rstrip() + entry + "\n"
    write(rel, text)


def update_decisions() -> None:
    rel = "docs/decisions/README.md"
    text = read(rel)
    entry = """

## D-011：被否定方案必须回写对应章节

- 状态：已确认
- 结论：弃用方案除保留在原始问答和变更日志外，还必须出现在相关系统章节，并标注“弃用想法”或“弃用名称”。
- 原因：让读者在查看当前设计时即可理解替代关系，避免旧想法被误认为遗漏或未来重新提出。

## D-012：新增名称候选“农场：无限”

- 状态：候选，未定名
- 结论：保留PvZ Infinite作为内部代号，同时把“农场：无限 / Farm: Infinite”列为原创名称候选。
- 原因：更贴合永久农场和无限成长，也有利于未来脱离既有IP。

## D-013：建立单文件无损HTML档案

- 状态：已确认
- 结论：仓库持续生成 `PvZ-Infinite-Archive.html`，完整嵌入除自身外的所有仓库文件，并提供校验、阅读、搜索、原文和本地编辑导出能力。
- 原因：降低文档分散带来的查看成本，同时不替代原文件和Git历史。
"""
    if "## D-011：被否定方案必须回写对应章节" not in text:
        text = text.rstrip() + entry + "\n"
    write(rel, text)


def main() -> None:
    update_master()
    update_core_loop()
    update_persistence_doc()
    update_readme()
    update_versioning()
    update_charter()
    update_changelog()
    update_decisions()
    print("Concept v0.3.1 incremental migration applied.")


if __name__ == "__main__":
    main()
