#!/usr/bin/env python3
"""Apply the Concept v0.4.0 incremental documentation migration.

The migration is idempotent and only edits the sections affected by the
plant-individuality, squad-control, multi-view, trade and AI-handover decisions.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def replace(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def insert_before(text: str, anchor: str, block: str, marker: str) -> str:
    if marker in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Missing insertion anchor: {anchor[:80]!r}")
    return text.replace(anchor, block.rstrip() + "\n\n" + anchor, 1)


def insert_after(text: str, anchor: str, block: str, marker: str) -> str:
    if marker in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Missing insertion anchor: {anchor[:80]!r}")
    return text.replace(anchor, anchor + "\n\n" + block.rstrip(), 1)


def update_readme() -> None:
    rel = "README.md"
    text = read(rel)
    text = replace(text, "Concept v0.3.1（2026-08-01）", "Concept v0.4.0（2026-08-01）")
    text = replace(text, "当前完整主游戏构思（Concept v0.3.1）", "当前完整主游戏构思（Concept v0.4.0）")

    core_anchor = "- 植物、炮塔、宠物和基础机器人主要自动工作；"
    core_block = """- 同种植物具有受控的自然形态差异，变异按根部、茎秆、枝叶、果实、表皮和核心器官模块组合；
- 永久变异进入基因库，可高成本DIY、复刻和授权；临时变异随夜间肉鸽卡牌在白天失效；
- 移动战斗型特定变异植物可成为独立个体，支持自动、上帝视角命令和直接接管；
- 当前小队验证上限为1名角色加4株移动战斗型植物；接管植物时，角色和其他植物默认跟随该植物；
- 人物、载具、机甲和适配植物以第一人称、第三人称、上帝视角为长期目标；
- 交易系统采用邻居交换、区域市场和基因/繁育授权的阶段化结构；"""
    text = insert_after(text, core_anchor, core_block, "当前小队验证上限为1名角色加4株")

    nav_anchor = "- [持久成长、自由主体与“凤凰计划”设计](docs/design/02-persistent-growth-player-avatar-and-phoenix.md)"
    nav_block = """- [植物个体、模块化变异、直接控制与交易系统](docs/design/03-plant-individuality-mutation-control-and-trade.md)
- [AI接手与协作规则](AGENTS.md)
- [项目增量工作流](docs/project-rules/WORKFLOW.md)
- [AI接手检查清单](docs/project-rules/AI-HANDOVER-CHECKLIST.md)
- [HTML与Pages规范](docs/project-rules/HTML-ARCHIVE-SPEC.md)"""
    text = insert_after(text, nav_anchor, nav_block, "植物个体、模块化变异、直接控制与交易系统")

    proto_anchor = "- 一个自由移动、自动攻击、可死亡和复活的玩家角色；"
    proto_block = """- 同种植物的基础形态差异；
- 1种永久变异模板、1种临时变异卡牌和1种移动战斗型独立植物；
- 玩家角色与移动植物的默认跟随、接管和编队锚点切换；
- 上帝视角与第三人称切换，第一人称作为后续目标；"""
    text = insert_after(text, proto_anchor, proto_block, "1种永久变异模板、1种临时变异卡牌")
    write(rel, text)


def update_master() -> None:
    rel = "docs/design/00-master-game-concept.md"
    text = read(rel)
    text = replace(text, "版本：Concept v0.3.1", "版本：Concept v0.4.0")

    pillar_anchor = "角色死亡会掉落资源和失去当前身体的临时强化；农场设施被摧毁会形成真实损失。稀有资产可通过基因库、组织样本、残骸和改装档案进行高成本、不完整恢复，避免一次意外删除全部长期故事。"
    pillar_block = """### 3.6 植物具有个体感、成长感、差异感和可塑性

同种植物具有自然形态差异；变异按部位模块组合；永久变异形成可保存和复刻的基因谱系；临时变异服务夜间肉鸽构筑。移动战斗型特定变异植物可升格为独立个体，在自动战斗、队伍跟随、上帝视角命令和玩家直接控制之间切换。"""
    text = insert_after(text, pillar_anchor, pillar_block, "### 3.6 植物具有个体感")

    mutation_anchor = "变异不能成为可轻易复制的固定升级路线。其触发受植物种类、土壤、天气、敌人污染、外星材料、邻近单位、卡牌和战斗事件共同影响。"
    mutation_block = """### 8.4 基础个体差异

同种植物至少在高矮、茎秆粗细、枝杈、叶片、直立程度、果实尺寸、色相和待机动作上存在受控差异。默认自然差异只影响外观，不形成隐藏数值最优解；只有明确标注的生长品质、疾病、年龄和基因词条才改变性能。

### 8.5 部位模块化变异

变异模块包括根部、茎秆与主体、枝叶、果实/投射器官、表皮防御、感知/核心器官。根部可产生移动、地热汲取、深层扎根、地下网络和净化等能力；果实可产生分裂、穿透、爆炸、电弧、酸液、追踪和召唤等变化。模块可以组合，但受到槽位、兼容性、能源、稳定度、维护和视觉可读性限制。

### 8.6 永久变异

永久变异基因进入基因库，可通过育种、组织培养和稀有材料进行抽取、组合、DIY、复刻和授权。植物个体仍会死亡、衰败和失控；基因保留不等于免费复活，复刻需要样本、设施、时间、资源和稳定校准，也不继承原个体的全部经历。

### 8.7 临时变异

临时变异不建立完全独立卡池，而作为普通肉鸽卡牌选择中可能出现的植物、道具、诱发因子、临时槽位或超频效果。玩家抽到后才提高相关变异出现或升级概率。临时变异在进入白天时与本轮肉鸽卡牌共同失效，除非触发极稀有且明确标注的基因固化事件。

> **弃用想法：当夜发生的所有变异只要植物存活就自动永久保留。** 当前明确区分永久变异与临时变异；未标注类型的变异不得默认永久化。

### 8.8 独立变异植物

具有移动、战斗、高智能或重要战术价值的特定变异植物可升格为独立个体，拥有独立状态、技能槽、个体卡牌、名字、谱系和战绩，并支持自动、驻守、巡逻、区域命令与玩家直接接管。普通静态植物继续自动工作，不要求逐株微操。"""
    text = insert_after(text, mutation_anchor, mutation_block, "### 8.4 基础个体差异")

    control_anchor = "- 同时保留WASD模式，避免鼠标跟随长时间使用造成疲劳。"
    control_block = """### 10.5 多视角

- 上帝视角：建设、全局观察、种植、编队和区域命令；
- 第三人称：玩家角色、载具、机甲和移动战斗型独立植物；
- 第一人称：人物、适配载具/机甲和具有合理观察器官的特殊植物。

最终目标支持三视角。原型优先上帝视角与第三人称，第一人称不阻塞核心塔防与小队系统。

### 10.6 角色与移动植物小队

当前原型和平衡验证上限为：**1名玩家角色 + 最多4株移动战斗型变异植物**。未被接管时，植物默认跟随玩家角色并自动战斗。玩家接管其中一株后，该植物成为临时编队锚点，原角色与其余植物默认跟随该植物、自动攻击和避险；玩家可快速切回人物或另一株植物。

原角色在AI跟随期间不会无敌，仍会受伤、死亡和掉落资源。玩家可在接管前下达角色留守、安全屋或载具驻留命令。上限是性能、可读性、寻路和战斗平衡的验证保护，后期只有在数据证明可控后才提高或取消。

> **弃用想法：项目从一开始完全不限制移动战斗植物数量。** 当前先采用1人+4植物上限，并允许在后期沙盒或终局测试中逐步放宽。

> **弃用想法：接管植物时玩家人物冻结或进入无敌状态。** 当前人物由AI跟随或留守，继续承担真实风险。"""
    text = insert_after(text, control_anchor, control_block, "### 10.5 多视角")

    trade_anchor = "## 22. 全方向塔防与路径"
    trade_block = """### 21.4 交易系统

交易系统分阶段开放：邻居/合作街区交换基础资源与普通种子；区域市场交易高级材料、样本、部件和可流通基因片段；后期通过有次数的基因模板、繁育许可、谱系授权和联合培育合同流通高阶永久变异。交易需要来源追踪、服务器权威结算、托管、税费、额度、绑定和反复制规则。真实货币交易当前不确认，终局战斗基因不得通过充值直接购买。

详细规则见 `docs/design/03-plant-individuality-mutation-control-and-trade.md`。"""
    text = insert_before(text, trade_anchor, trade_block, "### 21.4 交易系统")

    maintenance_anchor = "- 生成图、原始提示词、文件哈希和可还原资产均归档。"
    maintenance_block = """- 新AI或新对话必须先读取根目录 `AGENTS.md` 和 `docs/project-rules/`；
- Pages保持 `main / (root)`，根目录 `index.html` 进入最新总档案；
- HTML必须支持文本、图片、音频、视频、PDF及GLB/GLTF内嵌交互预览。"""
    text = insert_after(text, maintenance_anchor, maintenance_block, "新AI或新对话必须先读取根目录")
    write(rel, text)


def update_versioning() -> None:
    rel = "VERSIONING.md"
    text = read(rel)
    text = replace(text, "当前版本：`Concept v0.3.1`", "当前版本：`Concept v0.4.0`")
    roles_anchor = "- `VERSIONING.md`：本规则。"
    roles_block = """- `AGENTS.md`：AI代理和新对话的最高优先级接手规则；
- `docs/project-rules/`：详细工作流、接手清单和HTML规范；
- `index.html`：GitHub Pages根入口；"""
    text = insert_after(text, roles_anchor, roles_block, "`AGENTS.md`：AI代理")
    write(rel, text)


def update_changelog() -> None:
    rel = "CHANGELOG.md"
    text = read(rel)
    marker = "## Concept v0.4.0 — 2026-08-01"
    if marker not in text:
        block = """## Concept v0.4.0 — 2026-08-01

### 新增

- 新增植物自然个体差异与参数化外观规则；
- 新增根部、茎秆、枝叶、果实、表皮和感知核心的模块化变异体系；
- 新增永久变异基因库、DIY、复刻、谱系与高门槛授权；
- 新增临时变异作为普通肉鸽卡牌可能选项，并在进入白天时失效；
- 新增移动战斗型独立植物、个体卡牌和玩家直接接管；
- 新增1名角色加4株移动植物的验证编队、跟随与锚点切换；
- 新增人物、载具、机甲和适配植物的多视角目标；
- 新增邻居交换、区域市场和基因/繁育授权的阶段化交易系统；
- 新增 `AGENTS.md`、项目工作流、AI接手清单和HTML/Pages规范；
- HTML增加音频、视频、PDF、GLB和GLTF原位预览，并建立Pages根入口。

### 修改

- 细化“存活变异跨夜保留”：只有永久或已固化变异保留，临时变异随肉鸽卡牌失效；
- 直接控制植物时，玩家原角色与其他植物转由AI跟随当前锚点，但不获得无敌；
- 移动植物数量从“未来可无限”调整为先验证1+4上限，后续按性能和平衡数据放宽。

### 保持不变

- 永久农场、农业日循环、360°防御、自由主体、自动防御、无人农机、火种计划、合作和PvPvE大框架不变；
- 继续只做相关章节的增量修改，不重构已完成框架。
"""
        text = text.replace("本文件记录游戏构思的增量变化。完整原始语境见 `docs/conversations/`。", "本文件记录游戏构思的增量变化。完整原始语境见 `docs/conversations/`。\n\n" + block.rstrip(), 1)
    write(rel, text)


def update_decisions() -> None:
    rel = "docs/decisions/README.md"
    text = read(rel)
    if "## D-014：植物个体差异" not in text:
        text += """

## D-014：植物个体差异

- 状态：已确认
- 结论：同种植物具有受控的自然形态差异，默认只改变外观；明确的生长品质和基因词条才改变数值。

## D-015：永久与临时变异分层

- 状态：已确认
- 结论：永久变异进入基因库并可高成本DIY、复刻和授权；临时变异混入普通肉鸽卡牌选择，在进入白天时失效，除非明确触发基因固化。

## D-016：独立移动植物与编队

- 状态：已确认，数量待原型验证
- 结论：移动战斗型特定变异植物可成为独立个体。当前验证上限为1名角色加4株植物；默认跟随角色，接管植物后角色和其他植物跟随当前植物锚点。

## D-017：多视角目标

- 状态：方向已确认，分阶段实现
- 结论：人物、载具、机甲和适配植物以第一人称、第三人称和上帝视角为最终目标；原型优先上帝视角和第三人称。

## D-018：阶段化交易系统

- 状态：已确认进入设计，经济参数待验证
- 结论：先做邻居交换，再做区域市场，后做基因模板、繁育许可和谱系授权。所有高价值交易需要来源追踪、托管和反复制。

## D-019：AI接手与Pages规则

- 状态：已确认
- 结论：根目录 `AGENTS.md` 为AI接手最高优先级规则；Pages保持 `main / (root)`，`index.html` 进入持续更新的无损档案；档案支持多媒体、PDF和GLB/GLTF原位预览。
"""
    write(rel, text)


def update_conversation_index() -> None:
    rel = "docs/conversations/README.md"
    text = read(rel)
    anchor = "- [Round 005：弃用想法标注、名称候选与单文件HTML总档案](2026-08-01-round-005.md)"
    block = """- [Round 006：植物个体、永久/临时变异、交易与AI规则需求](2026-08-01-round-006.md)
- [Round 007：1人+4植物跟随接管微调与继续推进](2026-08-01-round-007.md)"""
    text = insert_after(text, anchor, block, "Round 006：植物个体")
    write(rel, text)


def main() -> None:
    update_readme()
    update_master()
    update_versioning()
    update_changelog()
    update_decisions()
    update_conversation_index()
    print("Applied Concept v0.4.0 incremental migration.")


if __name__ == "__main__":
    main()
