#!/usr/bin/env python3
"""Apply Concept v0.4.3 corrections for Master GDD navigation and Fireseed Plan.

Idempotent migration. It preserves the existing design body and only patches the
relevant sections, topic document, archive renderer, version references and
changelog.
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


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Missing replacement anchor for {label}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_i = text.find(start)
    end_i = text.find(end, start_i + len(start))
    if start_i < 0 or end_i < 0:
        raise RuntimeError(f"Missing section anchors for {label}")
    current = text[start_i:end_i]
    if replacement.strip() == current.strip():
        return text
    return text[:start_i] + replacement.rstrip() + "\n\n" + text[end_i:]


def update_master_gdd() -> None:
    rel = "docs/design/00-master-game-concept.md"
    text = read(rel)
    text = text.replace("版本：Concept v0.4.2", "版本：Concept v0.4.3", 1)
    text = text.replace("**当前概念版本**：Concept v0.4.2", "**当前概念版本**：Concept v0.4.3", 1)
    text = replace_once(
        text,
        "| 玩家主体与输入 | [方向确认·参数待验证] | 自由移动、自动攻击、点击交互；鼠标跟随与WASD并存方式待测 | 10 |",
        "| 玩家主体与输入 | [方向确认·参数待验证] | 自由移动、自动攻击、点击交互；鼠标跟随与WASD并存方式待测 | 10 |\n| 玩家身份呈现 | [已确认·后续留白] | 开局不完整解释人物来源和本质；允许后续按玩法需要补入生物变异、义体或共生改造 | 10、17 |",
        "player identity status row",
    )
    text = replace_once(
        text,
        "| 火种计划 | [方向确认·名称暂定] | 意识备份和有代价复生；技术来源、身体体系和设施层级待定 | 17 |",
        "| 火种计划 | [已确认·名称暂定] | 人物真实死亡触发意识上传至安全存储节点；地下实验室快速生成/启用克隆肉体并重新注入意识 | 17 |",
        "fireseed status row",
    )

    fireseed = r'''### 17. 角色死亡、身份留白与“火种计划”

“火种计划”就是此前讨论中受《瑞克和莫蒂》Operation Phoenix启发的原创复生系统暂定名。它不是普通医疗、重伤救援或把濒死人物抢救回来，而是：**人物真实死亡后，将意识/记忆状态上传或转移至安全存储节点，在家中地下实验室或其他受保护设施中迅速生成、启用一具克隆肉体，并把意识重新注入新身体。**

正式项目不直接使用“凤凰计划 / Operation Phoenix”名称和既有作品的具体世界观表达；“火种计划”目前作为原创工作名，最终名称仍可随世界观调整。

> **弃用想法：把火种计划弱化成高级医疗、普通复苏或单纯重伤救援。** 这会丢失“死亡后意识转移 + 克隆身体重建”的核心机制，已明确弃用。

> **弃用想法：在游戏开局完整说明玩家是纯数字意识、多身体载体或某种确定实验产物。** 当前应保留人物身份悬念，只展示玩家此刻能做什么，不提前锁死其来源、本质和全部改造上限。

#### 17.1 玩家身份呈现边界

- 游戏开局只需要建立一个可自定义、可行动、拥有农场和基础技术能力的玩家人物；
- 不必立即解释人物为何掌握复生技术、是否经历过实验、是否仍是普通人类；
- 身份线索可通过地下实验室、旧档案、异常身体反应、外星记录和剧情逐步出现；
- 后续如需要加入类似高强度生物变异、身体重构、机械义体或植物共生升级，可在不推翻前期设定的情况下继续补全；
- 玩家人格和长期档案保持连续，但“身体是否完全等同于原身体”“意识备份是否绝对连续”等哲学与剧情问题暂不强行给出唯一答案。

#### 17.2 火种计划核心流程

1. 玩家人物在世界中真实受伤、死亡，原身体不会被系统瞬间抹除；
2. 死亡事件触发意识/记忆状态向安全存储网络或本地受保护节点上传；
3. 家中地下实验室、实验谷仓或后期备用站调用预制培养体或高速生物制造设备；
4. 系统迅速生成或启用与玩家模板匹配的克隆肉体；
5. 意识被重新注入克隆体，玩家恢复直接行动；
6. 原尸体、装备、背包和未保险资源仍留在死亡地点，需要玩家、队友、机器人或宠物回收；
7. 农场植物、炮塔、动物、机器人和生产设施在复生期间继续按AI运行，也可能继续受损。

“死亡时一次性完整上传”还是“平时持续增量同步、死亡时完成最终同步”，属于技术和失败边界问题，尚待后续讨论；但无论采用哪种实现，都不能把火种计划改回普通医疗。

#### 17.3 与植物、机器人和机甲接管的关系

直接接管植物、机器人、载具或机甲，原则上属于**远程神经连接或战术接管**，而不是玩家人格永久迁入目标单位。

- 接管期间，玩家原身体仍然存在于世界中；
- 原身体可由AI跟随当前接管单位、前往掩体、留守设施或执行预设命令；
- 连接距离、中继塔、信号强度、干扰、建筑和能源可以形成限制；
- 被接管单位遭到摧毁，不等于玩家人格死亡，控制应回退到仍存活的原身体；
- 原身体在接管期间仍可受伤、死亡和掉落资源；
- 原身体死亡时，才触发真正的火种计划复生流程；
- 后期可存在极少数“深度意识转移”科技，但不作为基础接管规则。

#### 17.4 复生代价与待验证参数

火种计划应快速恢复玩家参与，而不是让玩家长时间旁观；但死亡仍需产生真实代价。当前确认的代价方向包括：

- 当前身体携带的临时人物加成、药剂、临时突变或未同步状态可能丢失；
- 未保险装备、背包和资源留在死亡地点；
- 克隆体生成或启用消耗电力、生物材料、培养体或身体库存；
- 复生设施可被断电、干扰、入侵或摧毁；
- 连续死亡可造成克隆不稳定、材料压力或短期身体异常。

具体复生秒数、是否预先培养空白身体、同步频率、连续死亡惩罚和全部设施失效后的处理方式仍待讨论，不在此阶段擅自定死。

#### 17.5 复生期间与设施失效

- 单人模式可暂时使用农场监控、侦察无人机、基础维修机器人或宠物摄像头观察和进行有限操作；
- 合作玩家可恢复供电、保护复生设施、运送培养材料或回收尸体；
- 主复生设施失效后，可以由后期备用站、移动复生舱或安全黑匣子接管，但具体优先级仍待确认；
- 若所有复生节点均不可用，游戏不应直接删除长期存档，但应进入明确的救援、恢复或阶段失败状态。

#### 17.6 后续人物改造与叙事空间

后期可按玩法需要逐步讨论：

- 类似强生物变异的玩家能力树；
- 机械义体、外星器官和植物共生改造；
- 克隆体出现随机差异或模板污染；
- 原尸体被僵尸感染、虫族吸收或外星人绑架；
- 意识数据被截获、复制或篡改；
- 多份备份同时激活引发身份冲突；
- 玩家主动选择特殊身体框架。

这些方向当前只保留接口和悬念，不在开局完整展示，也不阻塞首个原型。'''
    text = replace_between(text, "### 17. 角色死亡与“火种计划”", "## PART IV｜联机、经济与空间战斗", fireseed, "fireseed section")

    pending = r'''#### 26.1 已提出但仍待决定

1. **[待定] 正式名称**：是否采用“农场：无限 / Farm: Infinite”，以及最终英文名、中文名和世界观品牌；
2. **[待定] 第一人称覆盖范围**：哪些人物、载具、机甲和植物正式支持第一人称；
3. **[待定] 农机远征结构**：派遣自动结算、实时地图和远程接管各占多大比例；
4. **[待定] 火种计划技术边界**：意识同步频率、预制身体或即时制造、全部复生节点失效后的救援/失败规则；
5. **[待定] 玩家身体改造体系**：是否以及何时加入生物变异、机械义体、植物共生和外星改造；
6. **[待定] 尸体后续**：是否会被感染、绑架、克隆或吸收为敌方单位；
7. **[待定] 长期世界推进**：季节、迁移新县域、地区重建和软重置是否存在；
8. **[待定] PvPvE时长结构**：短局匹配、长局战役、异步区域冲突或多种并存；
9. **[待定] 奶牛损失边界**：永久死亡、受伤、逃散、繁殖、绑架和救援怎样区分；
10. **[待定] 真实货币交易**：当前未确认，不能默认开放。'''
    text = replace_between(text, "#### 26.1 已提出但仍待决定", "#### 26.2 方向已确认但必须通过原型验证", pending, "pending register")
    text = replace_once(text, "| C-017 | 火种计划复生 | 原身体和物资留在死亡地，复生消耗时间、能源和材料 |", "| C-017 | 火种计划复生 | 真实死亡触发意识上传，安全设施快速生成/启用克隆身体并重新注入意识；原身体和物资留在死亡地 |", "decision C-017")
    text = replace_once(text, "| C-023 | 历史与增量维护 | 原始对话永久保存，弃用想法回写原章节，主GDD唯一权威 |", "| C-023 | 历史与增量维护 | 原始对话永久保存，弃用想法回写原章节，主GDD唯一权威 |\n| C-024 | 玩家身份前期留白 | 开局不完整说明人物来源、本质和全部改造上限，为后续生物/机械/共生发展保留悬念 |\n| C-025 | 复生与单位接管分离 | 火种计划负责人物死亡后的克隆复生；植物、机器人和机甲采用远程神经连接，原身体继续存在并承担风险 |", "new decisions")
    text = replace_once(text, "| X-013 | 充值购买无限累积高能护罩战力能源 | 形成付费战力与离线资源优势 | 游戏内获得储能；付费优先外观和非战力内容 |", "| X-013 | 充值购买无限累积高能护罩战力能源 | 形成付费战力与离线资源优势 | 游戏内获得储能；付费优先外观和非战力内容 |\n| X-014 | 把火种计划解释为高级医疗或普通救援 | 偏离死亡后意识上传与克隆身体重建的核心灵感 | 真实死亡后上传意识，在安全设施中快速克隆并注入意识 |\n| X-015 | 开局完整锁定玩家为纯数字意识或确定实验产物 | 过早耗尽身份悬念并限制后续人物改造 | 前期只展示必要身份，按剧情和玩法逐步揭示 |", "new deprecated decisions")
    write(rel, text)


def update_topic_document() -> None:
    rel = "docs/design/02-persistent-growth-player-avatar-and-phoenix.md"
    text = read(rel)
    text = text.replace("更新时间：2026-08-01", "更新时间：2026-08-02", 1)
    replacement = r'''## 9. 原创化“火种计划”复生系统

“火种计划”就是此前受《瑞克和莫蒂》Operation Phoenix启发的原创复生机制工作名。其核心不是普通医疗，而是人物真实死亡后，将意识/记忆状态上传或转移到安全存储节点，在家中地下实验室等受保护设施中迅速生成或启用克隆肉体，再把意识注入新身体。

本项目不直接使用“凤凰计划 / Operation Phoenix”名称和既有作品的具体设定；当前暂用原创名称“火种计划”。

> **弃用名称：正式沿用“凤凰计划”或 Operation Phoenix。** 旧称仅保留在灵感说明和历史记录中。

> **弃用想法：把火种计划弱化成高级医疗、普通复苏或重伤救援。** 当前明确采用“死亡后意识上传 + 克隆身体重建 + 意识注入”的复生逻辑。

> **弃用想法：开局完整公开玩家是纯数字意识、多身体载体或确定实验产物。** 玩家身份前期保持必要留白，以便后续按玩法需要加入生物变异、机械义体、植物共生或其他改造。

### 9.1 身份与悬念

- 开局只展示可自定义人物、农场所有权和必要行动能力；
- 人物真实来源、火种计划历史和身体本质不一次性说明；
- 地下实验室、旧档案、异常反应和外星记录可逐步提供线索；
- 后续人物改造系统可以增量加入，不需要推翻前期设定。

### 9.2 基础流程

1. 玩家人物真实死亡，原身体留在死亡地点；
2. 死亡触发意识/记忆状态向安全存储网络或本地节点上传；
3. 地下实验室、实验谷仓或备用设施调用预制培养体或高速生物制造设备；
4. 系统快速生成或启用匹配模板的克隆肉体；
5. 意识被重新注入克隆体，玩家恢复行动；
6. 原装备、背包和未保险资源需要回收；
7. 农场在复生期间继续由植物、炮塔、宠物和机器人自动运行。

同步采用死亡时一次上传还是持续增量备份，仍待后续讨论。

### 9.3 与直接接管的区分

植物、机器人、载具和机甲采用远程神经连接或战术接管：

- 接管时原身体仍在世界中；
- 原身体可由AI跟随、避险、留守或返回安全设施；
- 接管单位被摧毁不等于玩家人格死亡；
- 原身体死亡才触发火种计划；
- 距离、中继、信号干扰和能源可限制接管；
- 后期深度意识转移只作为高级科技可能性，不是基础规则。

### 9.4 死亡代价

复生要快速恢复玩家参与，但仍具有真实代价：

- 当前身体的临时人物加成、药剂、临时突变或未同步状态可能丢失；
- 背包和未保险资源留在死亡地点；
- 克隆体需要电力、生物材料、培养体或身体库存；
- 连续死亡可造成材料压力、克隆不稳定或短期异常；
- 复生设施可能断电、遭到干扰、入侵或摧毁。

具体复生时间、身体库存、同步频率和全部节点失效规则仍待确认。

### 9.5 复生期间与后续叙事

- 单人可暂时使用监控、侦察无人机、基础机器人或宠物摄像头；
- 合作队友可恢复供电、运输材料、保护设施和回收尸体；
- 备用站、移动复生舱和安全黑匣子的优先级待讨论；
- 后期可讨论强生物变异、机械义体、植物共生、克隆污染、尸体感染、意识截获和多备份冲突；
- 上述内容不在游戏开局完整展示，也不阻塞首个原型。'''
    text = replace_between(text, "## 9. 原创化“凤凰计划”复活系统", "## 10. 平衡结论", replacement, "topic fireseed section")
    write(rel, text)


def update_archive_builder() -> None:
    rel = "tools/build_archive.py"
    text = read(rel)
    text = text.replace('CONCEPT_VERSION = "Concept v0.4.1"', 'CONCEPT_VERSION = "Concept v0.4.3"', 1)
    text = replace_once(text, '.gdd-toc ol{columns:2;column-gap:34px;margin:0;padding-left:22px}.gdd-toc li{break-inside:avoid;margin:4px 0}', '.gdd-toc-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.gdd-toc-part{break-inside:avoid;border:1px solid var(--line);border-radius:12px;padding:11px 13px;background:rgba(0,0,0,.13)}.gdd-toc-part>a{display:block;color:var(--green);font-weight:700;text-decoration:none;margin-bottom:5px}.gdd-toc-part ul{list-style:none;margin:0;padding:0}.gdd-toc-part li{margin:3px 0;padding-left:10px;border-left:2px solid rgba(111,231,237,.18)}', "toc css")
    text = replace_once(text, '@media(max-width:900px){.gdd-toc ol{columns:1}', '@media(max-width:900px){.gdd-toc-grid{grid-template-columns:1fr}', "toc responsive css")
    old_func = "function tocFor(src){const seen=new Map(),items=[];for(const line of src.replace(/\\r\\n/g,'\\n').split('\\n')){const m=line.match(/^(#{2,3})\\s+(.*)$/);if(!m)continue;const title=m[2].replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g,'$1').replace(/[*`]/g,'').trim();let id=slug(title),n=(seen.get(id)||0)+1;seen.set(id,n);if(n>1)id+='-'+n;items.push({level:m[1].length,title,id})}if(!items.length)return'';return '<nav class=\"gdd-toc\"><strong>Master GDD 章节目录</strong><ol>'+items.map(i=>`<li style=\"margin-left:${(i.level-2)*16}px\"><a href=\"#${i.id}\">${esc(i.title)}</a></li>`).join('')+'</ol></nav>'}"
    new_func = "function tocFor(src){const seen=new Map(),items=[];for(const line of src.replace(/\\r\\n/g,'\\n').split('\\n')){const m=line.match(/^(#{2,3})\\s+(.*)$/);if(!m)continue;const title=m[2].replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g,'$1').replace(/[*`]/g,'').trim();let id=slug(title),n=(seen.get(id)||0)+1;seen.set(id,n);if(n>1)id+='-'+n;items.push({level:m[1].length,title,id})}if(!items.length)return'';let out='<nav class=\"gdd-toc\"><strong>Master GDD 分卷目录</strong><div class=\"gdd-toc-grid\">',open=false;for(const item of items){if(item.level===2){if(open)out+='</ul></section>';out+=`<section class=\"gdd-toc-part\"><a href=\"#${item.id}\">${esc(item.title)}</a><ul>`;open=true}else if(open){out+=`<li><a href=\"#${item.id}\">${esc(item.title)}</a></li>`}}if(open)out+='</ul></section>';return out+'</div></nav>'}"
    text = replace_once(text, old_func, new_func, "toc function")
    write(rel, text)


def update_version_files() -> None:
    for rel in ("README.md", "AGENTS.md"):
        text = read(rel).replace("Concept v0.4.2", "Concept v0.4.3")
        write(rel, text)
    rel = "CHANGELOG.md"
    text = read(rel)
    marker = "## Concept v0.4.3 — 火种计划纠正与目录显示修复"
    if marker not in text:
        block = r'''## Concept v0.4.3 — 火种计划纠正与目录显示修复

### 新增

- 明确玩家身份在开局保持必要留白，不提前锁定为纯数字意识或确定实验产物；
- 为后续生物变异、机械义体、植物共生和外星改造保留增量扩展接口；
- 将“玩家身份前期留白”和“复生与单位接管分离”登记为已确认决策。

### 修改

- 纠正火种计划：人物真实死亡后触发意识上传，在安全地下实验室或备用设施中快速生成/启用克隆肉体并重新注入意识；
- 明确火种计划不是高级医疗、普通复苏或重伤救援；
- 明确植物、机器人、载具和机甲采用远程神经连接/战术接管，原身体继续存在并承担风险；
- 重写HTML的Master GDD目录为分卷卡片和章内链接，移除浏览器自动添加的重复数字序号；
- 将意识同步频率、克隆身体库存、全部复生节点失效规则和玩家后期改造体系保留为待定问题。

### 保持不变

- 不修改永久农场、农业日、360°防御、植物变异、小队、合作和PvPvE既有框架；
- 不删除此前错误建议，而是在对应章节和弃用总表中明确标记。

'''
        text = text.replace("## Concept v0.4.2 — Master GDD目录结构重构", block + "## Concept v0.4.2 — Master GDD目录结构重构", 1)
    write(rel, text)


def main() -> None:
    update_master_gdd()
    update_topic_document()
    update_archive_builder()
    update_version_files()
    print("Applied Concept v0.4.3 Fireseed Plan and TOC corrections.")


if __name__ == "__main__":
    main()
