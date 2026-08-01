#!/usr/bin/env python3
"""Build a self-contained, lossless HTML snapshot of the repository.

Every repository file except the generated HTML itself and .git internals is
embedded as base64 together with byte size, MIME type and SHA-256. Text files
can be read, searched, copied, edited locally and exported without changing the
source repository. Binary images and other assets can be previewed or restored.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OUTPUT = "PvZ-Infinite-Archive.html"
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".htm", ".xml",
    ".svg", ".csv", ".gitignore", ".gitattributes", ".editorconfig", ".sh",
    ".ps1", ".bat", ".sql", ".lock",
}
TEXT_NAMES = {"README", "LICENSE", "COPYING", "Makefile", "Dockerfile"}
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".idea", ".vscode"}


def is_text_file(path: Path, data: bytes) -> bool:
    if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if b"\x00" in data[:4096]:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def collect_files(root: Path, output: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    output_resolved = output.resolve()
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.resolve() == output_resolved:
            continue
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        text = is_text_file(path, data)
        if text and mime == "application/octet-stream":
            mime = "text/plain"
        items.append({
            "path": rel,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "mime": mime,
            "text": text,
            "data": base64.b64encode(data).decode("ascii"),
        })
    return items


def category_for(path: str) -> str:
    if path == "README.md": return "项目入口"
    if path.startswith("docs/design/"): return "游戏设计"
    if path.startswith("docs/conversations/"): return "完整对话"
    if path.startswith("docs/session-logs/"): return "讨论纪要"
    if path.startswith("docs/research/"): return "场景调研"
    if path.startswith("docs/decisions/"): return "设计决策"
    if path.startswith("assets/"): return "视觉资产"
    if path.startswith(".github/"): return "自动化"
    if path.startswith("tools/"): return "维护工具"
    return "项目治理"


def build_html(root: Path, output: Path) -> None:
    files = collect_files(root, output)
    for item in files:
        item["category"] = category_for(str(item["path"]))
    total_bytes = sum(int(item["size"]) for item in files)
    snapshot_digest = hashlib.sha256(
        "\n".join(f"{i['path']}:{i['sha256']}" for i in files).encode("utf-8")
    ).hexdigest()
    payload = {
        "title": "农场：无限 / PvZ Infinite 项目总档案",
        "conceptVersion": "Concept v0.3.1",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fileCount": len(files),
        "totalBytes": total_bytes,
        "snapshotSha256": snapshot_digest,
        "files": files,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    document = fr'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>农场：无限 / PvZ Infinite 项目总档案</title>
<style>
:root{{--bg:#07100d;--panel:rgba(10,25,20,.88);--panel2:rgba(14,34,27,.82);--line:rgba(120,255,188,.17);--green:#76f2a7;--cyan:#6fe7ed;--gold:#ffc866;--danger:#ff9f5b;--muted:#9eb7ac;--text:#eafff3;--shadow:0 20px 70px rgba(0,0,0,.38)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:radial-gradient(circle at 15% 0,#153c29 0,transparent 30%),radial-gradient(circle at 90% 10%,#123944 0,transparent 26%),linear-gradient(145deg,#06100d,#091713 54%,#040a08);color:var(--text);font:15px/1.75 Inter,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;min-height:100vh}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:linear-gradient(rgba(111,231,237,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(111,231,237,.06) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,black,transparent 88%)}}
button,input,textarea{{font:inherit}}a{{color:var(--cyan)}}.shell{{display:grid;grid-template-columns:330px minmax(0,1fr);min-height:100vh}}.side{{position:sticky;top:0;height:100vh;padding:24px 18px;border-right:1px solid var(--line);background:rgba(4,13,10,.9);backdrop-filter:blur(18px);overflow:auto;z-index:5}}.brand{{padding:18px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,rgba(118,242,167,.12),rgba(111,231,237,.04));box-shadow:var(--shadow);position:relative;overflow:hidden}}.brand:after{{content:"";position:absolute;width:170px;height:170px;border:1px solid rgba(118,242,167,.18);border-radius:50%;right:-90px;top:-90px;box-shadow:0 0 50px rgba(118,242,167,.15)}}.kicker{{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--green)}}h1{{font-size:23px;line-height:1.25;margin:.35rem 0}}.sub{{color:var(--muted);font-size:13px}}.stats{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px}}.stat{{padding:10px;border:1px solid var(--line);border-radius:13px;background:rgba(0,0,0,.18)}}.stat b{{display:block;color:var(--gold);font-size:17px}}.search{{margin:18px 0 10px}}.search input{{width:100%;border:1px solid var(--line);background:#08140f;color:var(--text);padding:12px 13px;border-radius:12px;outline:none}}.search input:focus{{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(111,231,237,.08)}}.filters{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}}.chip{{border:1px solid var(--line);background:rgba(118,242,167,.06);color:var(--muted);padding:5px 9px;border-radius:999px;cursor:pointer;font-size:12px}}.chip.active,.chip:hover{{color:#04110b;background:var(--green);border-color:var(--green)}}.file-list{{display:flex;flex-direction:column;gap:5px}}.file-btn{{text-align:left;border:1px solid transparent;background:transparent;color:#bed3c9;padding:9px 10px;border-radius:11px;cursor:pointer;word-break:break-all}}.file-btn:hover{{background:rgba(118,242,167,.06);border-color:var(--line)}}.file-btn.active{{background:linear-gradient(90deg,rgba(118,242,167,.17),rgba(111,231,237,.06));color:white;border-color:rgba(118,242,167,.28)}}.file-btn small{{display:block;color:#6f9383}}.main{{min-width:0;padding:0 28px 70px}}.hero{{min-height:290px;margin:0 -28px 24px;padding:44px 44px 34px;position:relative;overflow:hidden;border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(5,15,11,.98),rgba(8,27,20,.76) 55%,rgba(4,15,14,.91)),radial-gradient(circle at 70% 30%,rgba(111,231,237,.22),transparent 28%)}}.hero svg{{position:absolute;right:0;bottom:-12px;width:min(700px,55vw);height:auto;opacity:.42;filter:drop-shadow(0 0 20px rgba(118,242,167,.25))}}.hero-content{{position:relative;z-index:2;max-width:820px}}.hero h2{{font-size:clamp(32px,5vw,64px);line-height:1.03;margin:12px 0 14px;letter-spacing:-.04em}}.hero h2 span{{color:var(--green)}}.hero p{{font-size:17px;color:#c7ddd2;max-width:740px}}.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}}.badge{{padding:7px 11px;border-radius:999px;border:1px solid var(--line);background:rgba(0,0,0,.22);color:#cbf5dc;font-size:12px}}.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px;border:1px solid var(--line);border-radius:17px;background:var(--panel);position:sticky;top:14px;z-index:4;backdrop-filter:blur(16px);box-shadow:var(--shadow)}}.path{{min-width:0;font-weight:700;word-break:break-all}}.meta{{font-size:12px;color:var(--muted)}}.actions{{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}}.btn{{border:1px solid var(--line);background:rgba(118,242,167,.07);color:var(--text);padding:8px 11px;border-radius:10px;cursor:pointer}}.btn:hover{{border-color:var(--green);background:rgba(118,242,167,.15)}}.tabs{{display:flex;gap:8px;margin:18px 0 0}}.tab{{border:0;border-bottom:2px solid transparent;background:transparent;color:var(--muted);padding:9px 11px;cursor:pointer}}.tab.active{{color:var(--green);border-color:var(--green)}}.content-card{{margin-top:0;border:1px solid var(--line);border-radius:20px;background:var(--panel);box-shadow:var(--shadow);overflow:hidden}}.view{{display:none;padding:28px clamp(18px,4vw,52px)}}.view.active{{display:block}}.markdown{{max-width:1050px;margin:auto}}.markdown h1,.markdown h2,.markdown h3,.markdown h4{{line-height:1.3;scroll-margin-top:100px}}.markdown h1{{font-size:34px;border-bottom:1px solid var(--line);padding-bottom:14px}}.markdown h2{{font-size:25px;color:#d8ffe7;margin-top:2.3em;border-left:4px solid var(--green);padding-left:13px}}.markdown h3{{font-size:19px;color:var(--cyan);margin-top:1.8em}}.markdown p{{color:#d1e3da}}.markdown ul,.markdown ol{{padding-left:1.5em}}.markdown li{{margin:.28em 0}}.markdown code{{background:#07120e;border:1px solid rgba(118,242,167,.12);padding:.12em .35em;border-radius:6px;color:#b9ffd3}}.markdown pre{{overflow:auto;background:#030906;padding:18px;border-radius:15px;border:1px solid var(--line)}}.markdown pre code{{border:0;padding:0;background:transparent}}.markdown blockquote{{margin:1.3em 0;padding:13px 16px;border-left:4px solid var(--cyan);background:rgba(111,231,237,.07);border-radius:0 12px 12px 0}}.markdown blockquote.deprecated{{border-color:var(--danger);background:rgba(255,159,91,.09);box-shadow:inset 0 0 0 1px rgba(255,159,91,.08)}}.markdown blockquote.deprecated strong{{color:#ffc093}}.markdown table{{border-collapse:collapse;width:100%;overflow:auto;display:block}}.markdown td,.markdown th{{border:1px solid var(--line);padding:8px 10px}}.source,.editor{{width:100%;min-height:66vh;background:#030906;color:#d8fbe7;border:1px solid var(--line);border-radius:14px;padding:18px;font:13px/1.65 "Cascadia Code","SFMono-Regular",Consolas,monospace;resize:vertical;white-space:pre;overflow:auto}}pre.source{{margin:0}}.image-preview{{display:block;max-width:100%;max-height:74vh;margin:auto;border-radius:16px;border:1px solid var(--line)}}.binary-card{{padding:40px;text-align:center;color:var(--muted)}}.integrity{{margin-top:18px;padding:14px;border:1px dashed var(--line);border-radius:13px;color:var(--muted);font-size:12px;word-break:break-all}}.empty{{padding:70px;text-align:center;color:var(--muted)}}.footer{{text-align:center;color:#6d8d7f;padding:30px 0}}@media(max-width:900px){{.shell{{display:block}}.side{{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--line)}}.file-list{{max-height:280px;overflow:auto}}.main{{padding:0 14px 50px}}.hero{{margin:0 -14px 18px;padding:34px 20px}}.hero svg{{opacity:.2;width:100%}}.toolbar{{top:6px;align-items:flex-start;flex-direction:column}}.actions{{justify-content:flex-start}}}}
</style>
</head>
<body>
<div class="shell">
<aside class="side">
  <section class="brand"><div class="kicker">Living Design Archive</div><h1>农场：无限</h1><div class="sub">PvZ Infinite · 名称待定<br>永久农场 × 360°塔防 × 肉鸽成长</div><div class="stats"><div class="stat"><b id="fileCount"></b>文件</div><div class="stat"><b id="totalSize"></b>快照</div></div></section>
  <div class="search"><input id="search" placeholder="搜索文件名或全部内容…" aria-label="搜索"></div>
  <div class="filters" id="filters"></div>
  <nav class="file-list" id="fileList"></nav>
</aside>
<main class="main">
  <header class="hero">
    <svg viewBox="0 0 900 420" aria-hidden="true"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#76f2a7"/><stop offset="1" stop-color="#6fe7ed"/></linearGradient></defs><path d="M0 340H900" stroke="url(#g)" opacity=".35"/><path d="M40 340V220h150v120M70 220l45-70 45 70M235 340V150h85v190M250 150V95h55v55M360 340V190h150v150M390 190l45-72 45 72M550 340v-92h130v92M705 340V170h55v170M732 170V85" fill="none" stroke="url(#g)" stroke-width="5"/><circle cx="790" cy="72" r="48" fill="none" stroke="#6fe7ed" stroke-width="3"/><path d="M742 72h96M790 24v96M760 42l60 60M820 42l-60 60" stroke="#6fe7ed" opacity=".6"/><path d="M0 365c90-35 150 35 240 0s150 35 240 0 150 35 240 0 120 20 180 0" fill="none" stroke="#76f2a7" stroke-width="3" opacity=".45"/><ellipse cx="660" cy="80" rx="100" ry="25" fill="none" stroke="#6fe7ed" stroke-width="3"/><path d="M610 80l-38 120h176L710 80" fill="url(#g)" opacity=".08"/></svg>
    <div class="hero-content"><div class="kicker">Self-contained · Lossless · Searchable</div><h2>一份文件，保存整个<span>无限农场</span></h2><p>本页面无损嵌入仓库全部内容：主设计、被标注的弃用想法、逐轮对话、调研、决策、版本历史、维护工具与视觉资产。原文件字节和校验值均可恢复。</p><div class="badges"><span class="badge" id="versionBadge"></span><span class="badge" id="generatedBadge"></span><span class="badge" id="hashBadge"></span></div></div>
  </header>
  <section class="toolbar"><div><div class="path" id="currentPath">选择文件</div><div class="meta" id="currentMeta"></div></div><div class="actions"><button class="btn" id="copyBtn">复制</button><button class="btn" id="downloadBtn">导出文件</button><button class="btn" id="exportEditsBtn">导出本地修改</button></div></section>
  <div class="tabs"><button class="tab active" data-tab="read">阅读</button><button class="tab" data-tab="source">原文</button><button class="tab" data-tab="edit">本地编辑</button></div>
  <section class="content-card"><div class="view active" id="readView"><div class="empty">正在载入档案…</div></div><div class="view" id="sourceView"></div><div class="view" id="editView"></div></section>
  <div class="footer">本HTML不替代Git仓库；本地编辑仅保存在浏览器，可导出后再提交。输出文件自身不被递归嵌入。</div>
</main>
</div>
<script id="snapshot" type="application/json">{payload_json}</script>
<script>
const archive=JSON.parse(document.getElementById('snapshot').textContent);let current=null,currentTab='read',filter='全部',query='';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
function fmt(n){{if(n<1024)return n+' B';if(n<1048576)return(n/1024).toFixed(1)+' KB';return(n/1048576).toFixed(1)+' MB'}}
function bytes(b64){{const bin=atob(b64),arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);return arr}}
function textOf(f){{return new TextDecoder('utf-8').decode(bytes(f.data))}}
function esc(s){{return s.replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function inline(s){{let x=esc(s);x=x.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');return x}}
function md(src){{const lines=src.replace(/\r\n/g,'\n').split('\n');let out=[],para=[],list=null,code=false,codeLines=[];const flushP=()=>{{if(para.length){{out.push('<p>'+inline(para.join(' '))+'</p>');para=[]}}}};const closeList=()=>{{if(list){{out.push('</'+list+'>');list=null}}}};for(const line of lines){{if(line.startsWith('```')){{flushP();closeList();if(!code){{code=true;codeLines=[]}}else{{out.push('<pre><code>'+esc(codeLines.join('\n'))+'</code></pre>');code=false}}continue}}if(code){{codeLines.push(line);continue}}if(/^#{{1,6}}\s/.test(line)){{flushP();closeList();const m=line.match(/^(#{{1,6}})\s+(.*)$/),n=m[1].length;out.push(`<h${{n}}>${{inline(m[2])}}</h${{n}}>`);continue}}if(/^>\s?/.test(line)){{flushP();closeList();const q=line.replace(/^>\s?/,''),cl=/弃用想法|弃用名称|弃用/.test(q)?' deprecated':'';out.push('<blockquote class="'+cl.trim()+'">'+inline(q)+'</blockquote>');continue}}if(/^[-*+]\s+/.test(line)){{flushP();if(list!=='ul'){{closeList();list='ul';out.push('<ul>')}}out.push('<li>'+inline(line.replace(/^[-*+]\s+/,''))+'</li>');continue}}if(/^\d+\.\s+/.test(line)){{flushP();if(list!=='ol'){{closeList();list='ol';out.push('<ol>')}}out.push('<li>'+inline(line.replace(/^\d+\.\s+/,''))+'</li>');continue}}if(/^---+$/.test(line.trim())){{flushP();closeList();out.push('<hr>');continue}}if(!line.trim()){{flushP();closeList();continue}}para.push(line.trim())}}flushP();closeList();if(code)out.push('<pre><code>'+esc(codeLines.join('\n'))+'</code></pre>');return out.join('\n')}}
function categories(){{return ['全部',...new Set(archive.files.map(f=>f.category))]}}
function renderFilters(){{$('#filters').innerHTML=categories().map(c=>`<button class="chip ${{c===filter?'active':''}}" data-cat="${{esc(c)}}">${{esc(c)}}</button>`).join('');$$('.chip').forEach(b=>b.onclick=()=>{{filter=b.dataset.cat;renderFilters();renderList()}})}}
function matches(f){{if(filter!=='全部'&&f.category!==filter)return false;if(!query)return true;const q=query.toLowerCase();if(f.path.toLowerCase().includes(q)||f.category.toLowerCase().includes(q))return true;return f.text&&textOf(f).toLowerCase().includes(q)}}
function renderList(){{const files=archive.files.filter(matches);$('#fileList').innerHTML=files.map(f=>`<button class="file-btn ${{current&&current.path===f.path?'active':''}}" data-path="${{esc(f.path)}}">${{esc(f.path)}}<small>${{esc(f.category)}} · ${{fmt(f.size)}}</small></button>`).join('')||'<div class="empty">没有匹配内容</div>';$$('.file-btn').forEach(b=>b.onclick=()=>openFile(archive.files.find(f=>f.path===b.dataset.path)))}}
function renderRead(f,source){{const v=$('#readView');if(f.text){{const ext=f.path.split('.').pop().toLowerCase();if(['md','markdown'].includes(ext))v.innerHTML='<article class="markdown">'+md(source)+'</article>';else if(['html','htm','svg'].includes(ext))v.innerHTML='<div class="binary-card"><p>为安全起见，此HTML/SVG作为源代码展示。</p><pre class="source">'+esc(source)+'</pre></div>';else v.innerHTML='<pre class="source">'+esc(source)+'</pre>'}}else if(f.mime.startsWith('image/')){{v.innerHTML=`<img class="image-preview" src="data:${{f.mime}};base64,${{f.data}}" alt="${{esc(f.path)}}">`}}else{{v.innerHTML=`<div class="binary-card"><h2>二进制文件</h2><p>${{esc(f.mime)}} · ${{fmt(f.size)}}</p><p>可使用“导出文件”无损恢复。</p></div>`}}v.innerHTML+=`<div class="integrity">SHA-256：${{f.sha256}}<br>原始字节：${{f.size}} · MIME：${{esc(f.mime)}}</div>`}}
function openFile(f){{if(!f)return;current=f;const source=f.text?textOf(f):'';$('#currentPath').textContent=f.path;$('#currentMeta').textContent=`${{f.category}} · ${{fmt(f.size)}} · ${{f.sha256.slice(0,16)}}…`;renderRead(f,source);$('#sourceView').innerHTML=f.text?'<pre class="source">'+esc(source)+'</pre>':'<div class="binary-card">二进制文件请使用导出功能查看。</div>';const key='pvz-infinite-edit::'+archive.snapshotSha256+'::'+f.path;const saved=localStorage.getItem(key);$('#editView').innerHTML=f.text?`<textarea class="editor" id="editor" spellcheck="false"></textarea><div class="integrity">本地编辑不会自动写回GitHub。内容保存在当前浏览器 localStorage 中，导出后再提交。</div>`:'<div class="binary-card">二进制文件不提供文本编辑。</div>';if(f.text){{$('#editor').value=saved??source;$('#editor').oninput=e=>localStorage.setItem(key,e.target.value)}}renderList();setTab(currentTab)}}
function setTab(name){{currentTab=name;$$('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===name));$$('.view').forEach(v=>v.classList.remove('active'));$('#'+name+'View').classList.add('active')}}
function download(blob,name){{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}}
$('#search').oninput=e=>{{query=e.target.value.trim();renderList()}};$$('.tab').forEach(t=>t.onclick=()=>setTab(t.dataset.tab));
$('#copyBtn').onclick=async()=>{{if(!current)return;const val=current.text?(currentTab==='edit'&&$('#editor')?$('#editor').value:textOf(current)):current.data;await navigator.clipboard.writeText(val);$('#copyBtn').textContent='已复制';setTimeout(()=>$('#copyBtn').textContent='复制',1200)}};
$('#downloadBtn').onclick=()=>{{if(!current)return;let data;if(current.text&&currentTab==='edit'&&$('#editor'))data=new TextEncoder().encode($('#editor').value);else data=bytes(current.data);download(new Blob([data],{{type:current.mime}}),current.path.split('/').pop())}};
$('#exportEditsBtn').onclick=()=>{{const edits={{snapshot:archive.snapshotSha256,exportedAt:new Date().toISOString(),files:{{}}}};for(const f of archive.files){{if(!f.text)continue;const key='pvz-infinite-edit::'+archive.snapshotSha256+'::'+f.path,v=localStorage.getItem(key);if(v!==null&&v!==textOf(f))edits.files[f.path]=v}}download(new Blob([JSON.stringify(edits,null,2)],{{type:'application/json'}}),'PvZ-Infinite-local-edits.json')}};
$('#fileCount').textContent=archive.fileCount;$('#totalSize').textContent=fmt(archive.totalBytes);$('#versionBadge').textContent=archive.conceptVersion;$('#generatedBadge').textContent='生成 '+archive.generatedAt.replace('T',' ').replace('+00:00',' UTC');$('#hashBadge').textContent='快照 '+archive.snapshotSha256.slice(0,12);renderFilters();renderList();openFile(archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md')||archive.files[0]);
</script>
</body>
</html>'''
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"Built {output.relative_to(root)} with {len(files)} files, {total_bytes} source bytes.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Repository root; defaults to script parent parent")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output HTML path relative to root")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    build_html(root, output)


if __name__ == "__main__":
    main()
