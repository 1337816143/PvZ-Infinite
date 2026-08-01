#!/usr/bin/env python3
"""Build the PvZ-Infinite lossless HTML archive and GitHub Pages entry.

The archive embeds every repository file except itself and Git internals as
base64, with path, MIME type, byte length and SHA-256. It offers inline previews
for text, images, audio, video, PDF and GLB/GLTF models. The Pages index is
written before scanning, so its exact source is also preserved in the archive.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OUTPUT = "PvZ-Infinite-Archive.html"
DEFAULT_INDEX = "index.html"
CONCEPT_VERSION = "Concept v0.4.1"
MODEL_VIEWER_VERSION = "4.3.1"
MODEL_VIEWER_URL = (
    "https://ajax.googleapis.com/ajax/libs/model-viewer/"
    f"{MODEL_VIEWER_VERSION}/model-viewer.min.js"
)

TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".json", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".jsx", ".css", ".scss", ".html", ".htm", ".xml", ".svg", ".csv",
    ".gitignore", ".gitattributes", ".editorconfig", ".sh", ".ps1",
    ".bat", ".sql", ".lock", ".gltf", ".obj", ".mtl",
}
TEXT_NAMES = {"README", "LICENSE", "COPYING", "Makefile", "Dockerfile"}
EXCLUDED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".idea", ".vscode",
}

mimetypes.add_type("model/gltf-binary", ".glb")
mimetypes.add_type("model/gltf+json", ".gltf")
mimetypes.add_type("model/vnd.usdz+zip", ".usdz")
mimetypes.add_type("audio/wav", ".wav")
mimetypes.add_type("video/webm", ".webm")


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


def write_pages_index(root: Path, archive_name: str, index_name: str) -> Path:
    archive_href = html.escape(archive_name, quote=True)
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta http-equiv="refresh" content="0; url={archive_href}">
<title>农场：无限 · 项目总档案</title>
<style>
html,body{{height:100%;margin:0}}body{{display:grid;place-items:center;background:radial-gradient(circle at 30% 20%,#174832,#07110d 58%,#020604);color:#eafff3;font:16px/1.7 system-ui,"Segoe UI","Microsoft YaHei",sans-serif}}main{{width:min(720px,calc(100% - 40px));padding:36px;border:1px solid rgba(118,242,167,.25);border-radius:24px;background:rgba(7,20,15,.86);box-shadow:0 30px 100px rgba(0,0,0,.45)}}h1{{margin:0 0 10px;color:#76f2a7}}a{{color:#6fe7ed}}code{{color:#ffc866}}
</style>
<script>location.replace({json.dumps(archive_name, ensure_ascii=False)});</script>
</head>
<body><main><h1>农场：无限 / Farm: Infinite</h1><p>正在进入最新项目总档案。</p><p>没有自动跳转时，请打开 <a href="{archive_href}"><code>{archive_href}</code></a>。</p></main></body>
</html>
"""
    index_path = root / index_name
    index_path.write_text(page, encoding="utf-8", newline="\n")
    return index_path


def collect_files(root: Path, output: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    output_resolved = output.resolve()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel_path.parts):
            continue
        if path.resolve() == output_resolved:
            continue
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        text = is_text_file(path, data)
        if text and mime == "application/octet-stream":
            mime = "text/plain"
        items.append(
            {
                "path": rel_path.as_posix(),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "mime": mime,
                "text": text,
                "data": base64.b64encode(data).decode("ascii"),
            }
        )
    return items


def category_for(path: str) -> str:
    if path in {"README.md", "index.html"}:
        return "项目入口"
    if path in {"AGENT.md", "AGENTS.md"} or path.startswith("docs/project-rules/"):
        return "项目规则"
    if path.startswith("docs/design/"):
        return "游戏设计"
    if path.startswith("docs/conversations/"):
        return "完整对话"
    if path.startswith("docs/session-logs/"):
        return "讨论纪要"
    if path.startswith("docs/research/"):
        return "场景调研"
    if path.startswith("docs/decisions/"):
        return "设计决策"
    if path.startswith("assets/"):
        return "视觉与游戏资产"
    if path.startswith(".github/"):
        return "自动化"
    if path.startswith("tools/"):
        return "维护工具"
    return "项目治理"


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>农场：无限 / PvZ Infinite 项目总档案</title>
<script type="module" src="__MODEL_VIEWER_URL__"></script>
<style>
:root{--bg:#07100d;--panel:rgba(10,25,20,.9);--line:rgba(120,255,188,.17);--green:#76f2a7;--cyan:#6fe7ed;--gold:#ffc866;--danger:#ff9f5b;--muted:#9eb7ac;--text:#eafff3;--shadow:0 20px 70px rgba(0,0,0,.38)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(circle at 15% 0,#153c29 0,transparent 30%),radial-gradient(circle at 90% 10%,#123944 0,transparent 26%),linear-gradient(145deg,#06100d,#091713 54%,#040a08);color:var(--text);font:15px/1.75 Inter,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;min-height:100vh}body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:linear-gradient(rgba(111,231,237,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(111,231,237,.06) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,black,transparent 88%)}button,input,textarea{font:inherit}a{color:var(--cyan)}
.shell{display:grid;grid-template-columns:340px minmax(0,1fr);min-height:100vh}.side{position:sticky;top:0;height:100vh;padding:24px 18px;border-right:1px solid var(--line);background:rgba(4,13,10,.92);backdrop-filter:blur(18px);overflow:auto;z-index:5}.brand{padding:18px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,rgba(118,242,167,.12),rgba(111,231,237,.04));box-shadow:var(--shadow);position:relative;overflow:hidden}.brand:after{content:"";position:absolute;width:170px;height:170px;border:1px solid rgba(118,242,167,.18);border-radius:50%;right:-90px;top:-90px;box-shadow:0 0 50px rgba(118,242,167,.15)}.kicker{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--green)}h1{font-size:23px;line-height:1.25;margin:.35rem 0}.sub{color:var(--muted);font-size:13px}.stats{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px}.stat{padding:10px;border:1px solid var(--line);border-radius:13px;background:rgba(0,0,0,.18)}.stat b{display:block;color:var(--gold);font-size:17px}.search{margin:18px 0 10px}.search input{width:100%;border:1px solid var(--line);background:#08140f;color:var(--text);padding:12px 13px;border-radius:12px;outline:none}.search input:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(111,231,237,.08)}.filters{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}.chip{border:1px solid var(--line);background:rgba(118,242,167,.06);color:var(--muted);padding:5px 9px;border-radius:999px;cursor:pointer;font-size:12px}.chip.active,.chip:hover{color:#04110b;background:var(--green);border-color:var(--green)}.file-list{display:flex;flex-direction:column;gap:5px}.file-btn{text-align:left;border:1px solid transparent;background:transparent;color:#bed3c9;padding:9px 10px;border-radius:11px;cursor:pointer;word-break:break-all}.file-btn:hover{background:rgba(118,242,167,.06);border-color:var(--line)}.file-btn.active{background:linear-gradient(90deg,rgba(118,242,167,.17),rgba(111,231,237,.06));color:white;border-color:rgba(118,242,167,.28)}.file-btn small{display:block;color:#6f9383}.main{min-width:0;padding:0 28px 70px}
.hero{min-height:290px;margin:0 -28px 24px;padding:44px 44px 34px;position:relative;overflow:hidden;border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(5,15,11,.98),rgba(8,27,20,.76) 55%,rgba(4,15,14,.91)),radial-gradient(circle at 70% 30%,rgba(111,231,237,.22),transparent 28%)}.hero svg{position:absolute;right:0;bottom:-12px;width:min(700px,55vw);height:auto;opacity:.42;filter:drop-shadow(0 0 20px rgba(118,242,167,.25))}.hero-content{position:relative;z-index:2;max-width:850px}.hero h2{font-size:clamp(32px,5vw,64px);line-height:1.03;margin:12px 0 14px;letter-spacing:-.04em}.hero h2 span{color:var(--green)}.hero p{font-size:17px;color:#c7ddd2;max-width:760px}.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}.badge{padding:7px 11px;border-radius:999px;border:1px solid var(--line);background:rgba(0,0,0,.22);color:#cbf5dc;font-size:12px}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px;border:1px solid var(--line);border-radius:17px;background:var(--panel);position:sticky;top:14px;z-index:4;backdrop-filter:blur(16px);box-shadow:var(--shadow)}.path{min-width:0;font-weight:700;word-break:break-all}.meta{font-size:12px;color:var(--muted)}.actions{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.btn{border:1px solid var(--line);background:rgba(118,242,167,.07);color:var(--text);padding:8px 11px;border-radius:10px;cursor:pointer}.btn:hover{border-color:var(--green);background:rgba(118,242,167,.15)}.tabs{display:flex;gap:8px;margin:18px 0 0}.tab{border:0;border-bottom:2px solid transparent;background:transparent;color:var(--muted);padding:9px 11px;cursor:pointer}.tab.active{color:var(--green);border-color:var(--green)}.content-card{border:1px solid var(--line);border-radius:20px;background:var(--panel);box-shadow:var(--shadow);overflow:hidden}.view{display:none;padding:28px clamp(18px,4vw,52px)}.view.active{display:block}
.markdown{max-width:1080px;margin:auto}.markdown h1,.markdown h2,.markdown h3,.markdown h4{line-height:1.3;scroll-margin-top:100px}.markdown h1{font-size:34px;border-bottom:1px solid var(--line);padding-bottom:14px}.markdown h2{font-size:25px;color:#d8ffe7;margin-top:2.3em;border-left:4px solid var(--green);padding-left:13px}.markdown h3{font-size:19px;color:var(--cyan);margin-top:1.8em}.markdown p{color:#d1e3da}.markdown ul,.markdown ol{padding-left:1.5em}.markdown li{margin:.28em 0}.markdown code{background:#07120e;border:1px solid rgba(118,242,167,.12);padding:.12em .35em;border-radius:6px;color:#b9ffd3}.markdown pre,.source{overflow:auto;background:#030906;padding:18px;border-radius:15px;border:1px solid var(--line)}.markdown pre code{border:0;padding:0;background:transparent}.markdown blockquote{margin:1.3em 0;padding:13px 16px;border-left:4px solid var(--cyan);background:rgba(111,231,237,.07);border-radius:0 12px 12px 0}.markdown blockquote.deprecated{border-color:var(--danger);background:rgba(255,159,91,.09);box-shadow:inset 0 0 0 1px rgba(255,159,91,.08)}.markdown blockquote.deprecated strong{color:#ffc093}.markdown table{border-collapse:collapse;width:100%;overflow:auto;display:block}.markdown td,.markdown th{border:1px solid var(--line);padding:8px 10px}.source,.editor{width:100%;min-height:66vh;color:#d8fbe7;font:13px/1.65 "Cascadia Code","SFMono-Regular",Consolas,monospace;white-space:pre;overflow:auto}.editor{background:#030906;border:1px solid var(--line);border-radius:14px;padding:18px;resize:vertical}.preview-wrap{display:grid;gap:16px}.image-preview{display:block;max-width:100%;max-height:76vh;margin:auto;border-radius:16px;border:1px solid var(--line)}audio,video{display:block;width:min(100%,980px);margin:auto;border-radius:14px;background:#020604}video{max-height:76vh}.pdf-preview{width:100%;height:76vh;border:1px solid var(--line);border-radius:16px;background:white}model-viewer{display:block;width:100%;height:min(76vh,760px);min-height:480px;border:1px solid var(--line);border-radius:16px;background:radial-gradient(circle at 50% 25%,#173f32,#040806 70%);--poster-color:transparent}.model-help{color:var(--muted);text-align:center}.binary-card{padding:40px;text-align:center;color:var(--muted)}.gdd-toc{max-width:1080px;margin:0 auto 18px;padding:18px 20px;border:1px solid rgba(111,231,237,.22);border-radius:16px;background:linear-gradient(145deg,rgba(111,231,237,.08),rgba(118,242,167,.04))}.gdd-toc strong{display:block;color:var(--green);margin-bottom:8px}.gdd-toc ol{columns:2;column-gap:34px;margin:0;padding-left:22px}.gdd-toc li{break-inside:avoid;margin:4px 0}.gdd-toc a{color:#c9f7dd;text-decoration:none}.gdd-toc a:hover{color:var(--cyan);text-decoration:underline}.binary-card{padding:40px;text-align:center;color:var(--muted)}.integrity{margin-top:18px;padding:14px;border:1px dashed var(--line);border-radius:13px;color:var(--muted);font-size:12px;word-break:break-all}.empty{padding:70px;text-align:center;color:var(--muted)}.error{padding:18px;border:1px solid rgba(255,159,91,.4);border-radius:14px;background:rgba(255,159,91,.08);color:#ffd1ae}.footer{text-align:center;color:#6d8d7f;padding:30px 0}
@media(max-width:900px){.gdd-toc ol{columns:1}.shell{display:block}.side{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--line)}.file-list{max-height:300px;overflow:auto}.main{padding:0 14px 50px}.hero{margin:0 -14px 18px;padding:34px 20px}.hero svg{opacity:.2;width:100%}.toolbar{top:6px;align-items:flex-start;flex-direction:column}.actions{justify-content:flex-start}model-viewer{min-height:360px}}
</style>
</head>
<body>
<div class="shell">
<aside class="side">
<section class="brand"><div class="kicker">Living Design Archive</div><h1>农场：无限</h1><div class="sub">PvZ Infinite · 名称待定<br>永久农场 × 植物小队 × 多视角</div><div class="stats"><div class="stat"><b id="fileCount"></b>文件</div><div class="stat"><b id="totalSize"></b>快照</div></div></section>
<div class="search"><input id="search" placeholder="搜索文件名或全部内容…" aria-label="搜索"></div><div class="filters" id="filters"></div><nav class="file-list" id="fileList"></nav>
</aside>
<main class="main">
<header class="hero"><svg viewBox="0 0 900 420" aria-hidden="true"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#76f2a7"/><stop offset="1" stop-color="#6fe7ed"/></linearGradient></defs><path d="M0 340H900" stroke="url(#g)" opacity=".35"/><path d="M40 340V220h150v120M70 220l45-70 45 70M235 340V150h85v190M250 150V95h55v55M360 340V190h150v150M390 190l45-72 45 72M550 340v-92h130v92M705 340V170h55v170M732 170V85" fill="none" stroke="url(#g)" stroke-width="5"/><circle cx="790" cy="72" r="48" fill="none" stroke="#6fe7ed" stroke-width="3"/><path d="M742 72h96M790 24v96M760 42l60 60M820 42l-60 60" stroke="#6fe7ed" opacity=".6"/><path d="M0 365c90-35 150 35 240 0s150 35 240 0 150 35 240 0 120 20 180 0" fill="none" stroke="#76f2a7" stroke-width="3" opacity=".45"/><ellipse cx="660" cy="80" rx="100" ry="25" fill="none" stroke="#6fe7ed" stroke-width="3"/><path d="M610 80l-38 120h176L710 80" fill="url(#g)" opacity=".08"/></svg><div class="hero-content"><div class="kicker">Lossless · Searchable · Media & 3D Ready</div><h2>一份入口，查看整个<span>无限农场</span></h2><p>默认打开唯一权威Master GDD，集中浏览已确认、待验证、待定、弃用与范围边界；同时无损嵌入AI规则、逐轮对话、版本历史、代码和全部资产。</p><div class="badges"><span class="badge" id="versionBadge"></span><span class="badge" id="generatedBadge"></span><span class="badge" id="hashBadge"></span><span class="badge">model-viewer __MODEL_VIEWER_VERSION__</span></div></div></header>
<section class="toolbar"><div><div class="path" id="currentPath">选择文件</div><div class="meta" id="currentMeta"></div></div><div class="actions"><button class="btn" id="masterBtn">主游戏设计</button><button class="btn" id="rulesBtn">AI规则</button><button class="btn" id="copyBtn">复制</button><button class="btn" id="downloadBtn">导出文件</button><button class="btn" id="exportEditsBtn">导出本地修改</button></div></section>
<div class="tabs"><button class="tab active" data-tab="read">阅读/预览</button><button class="tab" data-tab="source">原文</button><button class="tab" data-tab="edit">本地编辑</button></div>
<section class="content-card"><div class="view active" id="readView"><div class="empty">正在载入档案…</div></div><div class="view" id="sourceView"></div><div class="view" id="editView"></div></section>
<div class="footer">本地编辑不会自动写回GitHub。档案输出自身不递归嵌入；Pages入口文件已纳入快照。</div>
</main></div>
<script id="snapshot" type="application/json">__PAYLOAD__</script>
<script>
const archive=JSON.parse(document.getElementById('snapshot').textContent);let current=null,currentTab='read',filter='全部',query='';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];const textCache=new Map(),urlCache=new Map();
function fmt(n){if(n<1024)return n+' B';if(n<1048576)return(n/1024).toFixed(1)+' KB';return(n/1048576).toFixed(1)+' MB'}
function bytes(b64){const bin=atob(b64),arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);return arr}
function textOf(f){if(!textCache.has(f.path))textCache.set(f.path,new TextDecoder('utf-8').decode(bytes(f.data)));return textCache.get(f.path)}
function blobUrl(f){if(!urlCache.has(f.path))urlCache.set(f.path,URL.createObjectURL(new Blob([bytes(f.data)],{type:f.mime})));return urlCache.get(f.path)}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function inline(s){let x=esc(s);x=x.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');return x}
function slug(s){return String(s).replace(/`/g,'').replace(/\*+/g,'').trim().toLowerCase().replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu,'-').replace(/^-+|-+$/g,'')||'section'}
function tocFor(src){const seen=new Map(),items=[];for(const line of src.replace(/\r\n/g,'\n').split('\n')){const m=line.match(/^(#{2,3})\s+(.*)$/);if(!m)continue;const title=m[2].replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*`]/g,'').trim();let id=slug(title),n=(seen.get(id)||0)+1;seen.set(id,n);if(n>1)id+='-'+n;items.push({level:m[1].length,title,id})}if(!items.length)return'';return '<nav class="gdd-toc"><strong>Master GDD 章节目录</strong><ol>'+items.map(i=>`<li style="margin-left:${(i.level-2)*16}px"><a href="#${i.id}">${esc(i.title)}</a></li>`).join('')+'</ol></nav>'}
function md(src){
 const lines=src.replace(/\r\n/g,'\n').split('\n'),seen=new Map();let out=[],para=[],list=null,code=false,codeLines=[];
 const flushP=()=>{if(para.length){out.push('<p>'+inline(para.join(' '))+'</p>');para=[]}};
 const closeList=()=>{if(list){out.push('</'+list+'>');list=null}};
 const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(x=>x.trim());
 for(let i=0;i<lines.length;i++){
  const line=lines[i],next=lines[i+1]||'';
  if(line.startsWith('```')){flushP();closeList();if(!code){code=true;codeLines=[]}else{out.push('<pre><code>'+esc(codeLines.join('\n'))+'</code></pre>');code=false}continue}
  if(code){codeLines.push(line);continue}
  if(line.includes('|')&&/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(next)){
   flushP();closeList();const head=cells(line);i+=2;const rows=[];
   while(i<lines.length&&lines[i].includes('|')&&lines[i].trim()){rows.push(cells(lines[i]));i++}i--;
   out.push('<div style="overflow:auto"><table><thead><tr>'+head.map(c=>'<th>'+inline(c)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+head.map((_,j)=>'<td>'+inline(r[j]||'')+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>');continue
  }
  if(/^#{1,6}\s/.test(line)){flushP();closeList();const m=line.match(/^(#{1,6})\s+(.*)$/),n=m[1].length,title=m[2].replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*`]/g,'').trim();let id=slug(title),count=(seen.get(id)||0)+1;seen.set(id,count);if(count>1)id+='-'+count;out.push(`<h${n} id="${id}">${inline(m[2])}</h${n}>`);continue}
  if(/^>\s?/.test(line)){flushP();closeList();const q=line.replace(/^>\s?/,''),cl=/弃用想法|弃用名称|弃用/.test(q)?' deprecated':'';out.push('<blockquote class="'+cl.trim()+'">'+inline(q)+'</blockquote>');continue}
  if(/^[-*+]\s+/.test(line)){flushP();if(list!=='ul'){closeList();list='ul';out.push('<ul>')}out.push('<li>'+inline(line.replace(/^[-*+]\s+/,''))+'</li>');continue}
  if(/^\d+\.\s+/.test(line)){flushP();if(list!=='ol'){closeList();list='ol';out.push('<ol>')}out.push('<li>'+inline(line.replace(/^\d+\.\s+/,''))+'</li>');continue}
  if(/^---+$/.test(line.trim())){flushP();closeList();out.push('<hr>');continue}
  if(!line.trim()){flushP();closeList();continue}
  para.push(line.trim())
 }
 flushP();closeList();if(code)out.push('<pre><code>'+esc(codeLines.join('\n'))+'</code></pre>');return out.join('\n')
}
function extOf(f){const name=f.path.split('/').pop();return name.includes('.')?name.split('.').pop().toLowerCase():''}
function normalizePath(path){const stack=[];for(const part of path.split('/')){if(!part||part==='.')continue;if(part==='..')stack.pop();else stack.push(part)}return stack.join('/')}
function resolveRel(basePath,uri){if(/^(data:|blob:|https?:|#)/i.test(uri))return uri;let decoded=uri;try{decoded=decodeURIComponent(uri)}catch{}const dir=basePath.split('/').slice(0,-1).join('/');return normalizePath((dir?dir+'/':'')+decoded)}
function dataUrl(f){return `data:${f.mime};base64,${f.data}`}
async function modelUrl(f){if(extOf(f)==='glb')return blobUrl(f);const model=JSON.parse(textOf(f));const missing=[];for(const group of ['buffers','images']){for(const item of model[group]||[]){if(!item.uri||/^(data:|blob:|https?:)/i.test(item.uri))continue;const target=resolveRel(f.path,item.uri),dep=archive.files.find(x=>x.path===target);if(dep)item.uri=dataUrl(dep);else missing.push(target)}}if(missing.length)throw new Error('GLTF缺少依赖：'+missing.join('、'));return URL.createObjectURL(new Blob([JSON.stringify(model)],{type:'model/gltf+json'}))}
function categories(){return ['全部',...new Set(archive.files.map(f=>f.category))]}
function renderFilters(){$('#filters').innerHTML=categories().map(c=>`<button class="chip ${c===filter?'active':''}" data-cat="${esc(c)}">${esc(c)}</button>`).join('');$$('.chip').forEach(b=>b.onclick=()=>{filter=b.dataset.cat;renderFilters();renderList()})}
function matches(f){if(filter!=='全部'&&f.category!==filter)return false;if(!query)return true;const q=query.toLowerCase();if(f.path.toLowerCase().includes(q)||f.category.toLowerCase().includes(q)||f.mime.toLowerCase().includes(q))return true;return f.text&&textOf(f).toLowerCase().includes(q)}
function renderList(){const files=archive.files.filter(matches);$('#fileList').innerHTML=files.map(f=>`<button class="file-btn ${current&&current.path===f.path?'active':''}" data-path="${esc(f.path)}">${esc(f.path)}<small>${esc(f.category)} · ${fmt(f.size)}</small></button>`).join('')||'<div class="empty">没有匹配内容</div>';$$('.file-btn').forEach(b=>b.onclick=()=>openFile(archive.files.find(f=>f.path===b.dataset.path)))}
function integrity(f){return `<div class="integrity">SHA-256：${f.sha256}<br>原始字节：${f.size} · MIME：${esc(f.mime)}</div>`}
async function renderRead(f,source){const v=$('#readView'),ext=extOf(f);v.innerHTML='<div class="empty">正在准备预览…</div>';try{if(ext==='glb'||ext==='gltf'){v.innerHTML=`<div class="preview-wrap"><model-viewer id="modelPreview" camera-controls touch-action="pan-y" auto-rotate shadow-intensity="1" environment-image="neutral" interaction-prompt="auto" alt="${esc(f.path)}"></model-viewer><div class="model-help">拖动旋转 · 滚轮/手势缩放 · 右键或双指平移</div><div id="modelError"></div></div>`+integrity(f);const mv=$('#modelPreview');mv.addEventListener('error',()=>{$('#modelError').innerHTML='<div class="error">模型加载失败。请检查模型格式、关联纹理、缓冲文件或浏览器WebGL支持。</div>'});mv.src=await modelUrl(f)}else if(f.mime.startsWith('image/')){v.innerHTML=`<img class="image-preview" src="${blobUrl(f)}" alt="${esc(f.path)}">`+integrity(f)}else if(f.mime.startsWith('audio/')){v.innerHTML=`<div class="preview-wrap"><audio controls preload="metadata" src="${blobUrl(f)}"></audio></div>`+integrity(f)}else if(f.mime.startsWith('video/')){v.innerHTML=`<div class="preview-wrap"><video controls preload="metadata" src="${blobUrl(f)}"></video></div>`+integrity(f)}else if(f.mime==='application/pdf'||ext==='pdf'){v.innerHTML=`<iframe class="pdf-preview" src="${blobUrl(f)}" title="${esc(f.path)}"></iframe>`+integrity(f)}else if(f.text){if(['md','markdown'].includes(ext)){const toc=f.path==='docs/design/00-master-game-concept.md'?tocFor(source):'';v.innerHTML=toc+'<article class="markdown">'+md(source)+'</article>'+integrity(f)}else if(['html','htm','svg'].includes(ext))v.innerHTML='<div class="binary-card"><p>为安全起见，此文件在阅读模式中展示源代码。</p></div><pre class="source">'+esc(source)+'</pre>'+integrity(f);else v.innerHTML='<pre class="source">'+esc(source)+'</pre>'+integrity(f)}else{v.innerHTML=`<div class="binary-card"><h2>暂未提供内嵌渲染器</h2><p>${esc(f.mime)} · ${fmt(f.size)}</p><p>可使用“导出文件”无损恢复。OBJ、FBX和USDZ可在后续迭代增加专用预览。</p></div>`+integrity(f)}}catch(err){v.innerHTML=`<div class="error"><strong>预览失败</strong><br>${esc(err.message||String(err))}</div>`+integrity(f)}}
async function openFile(f){if(!f)return;current=f;const source=f.text?textOf(f):'';$('#currentPath').textContent=f.path;$('#currentMeta').textContent=`${f.category} · ${fmt(f.size)} · ${f.mime} · ${f.sha256.slice(0,16)}…`;await renderRead(f,source);$('#sourceView').innerHTML=f.text?'<pre class="source">'+esc(source)+'</pre>':'<div class="binary-card">二进制文件请使用阅读预览或导出功能。</div>';const key='pvz-infinite-edit::'+archive.snapshotSha256+'::'+f.path,saved=localStorage.getItem(key);$('#editView').innerHTML=f.text?'<textarea class="editor" id="editor" spellcheck="false"></textarea><div class="integrity">本地编辑保存在当前浏览器，导出后再提交。</div>':'<div class="binary-card">二进制文件不提供文本编辑。</div>';if(f.text){$('#editor').value=saved??source;$('#editor').oninput=e=>localStorage.setItem(key,e.target.value)}renderList();setTab(currentTab)}
function setTab(name){currentTab=name;$$('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===name));$$('.view').forEach(v=>v.classList.remove('active'));$('#'+name+'View').classList.add('active')}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$('#search').oninput=e=>{query=e.target.value.trim();renderList()};$$('.tab').forEach(t=>t.onclick=()=>setTab(t.dataset.tab));
$('#masterBtn').onclick=()=>openFile(archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md'));$('#rulesBtn').onclick=()=>openFile(archive.files.find(f=>f.path==='AGENTS.md'));
$('#copyBtn').onclick=async()=>{if(!current)return;const val=current.text?(currentTab==='edit'&&$('#editor')?$('#editor').value:textOf(current)):current.data;await navigator.clipboard.writeText(val);$('#copyBtn').textContent='已复制';setTimeout(()=>$('#copyBtn').textContent='复制',1200)};
$('#downloadBtn').onclick=()=>{if(!current)return;let data;if(current.text&&currentTab==='edit'&&$('#editor'))data=new TextEncoder().encode($('#editor').value);else data=bytes(current.data);download(new Blob([data],{type:current.mime}),current.path.split('/').pop())};
$('#exportEditsBtn').onclick=()=>{const edits={snapshot:archive.snapshotSha256,exportedAt:new Date().toISOString(),files:{}};for(const f of archive.files){if(!f.text)continue;const key='pvz-infinite-edit::'+archive.snapshotSha256+'::'+f.path,v=localStorage.getItem(key);if(v!==null&&v!==textOf(f))edits.files[f.path]=v}download(new Blob([JSON.stringify(edits,null,2)],{type:'application/json'}),'PvZ-Infinite-local-edits.json')};
$('#fileCount').textContent=archive.fileCount;$('#totalSize').textContent=fmt(archive.totalBytes);$('#versionBadge').textContent=archive.conceptVersion;$('#generatedBadge').textContent='生成 '+archive.generatedAt.replace('T',' ').replace('+00:00',' UTC');$('#hashBadge').textContent='快照 '+archive.snapshotSha256.slice(0,12);renderFilters();renderList();openFile(archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md')||archive.files.find(f=>f.path==='AGENTS.md')||archive.files[0]);
</script>
</body>
</html>'''


def build_html(root: Path, output: Path, index_name: str) -> None:
    write_pages_index(root, output.name, index_name)
    files = collect_files(root, output)
    for item in files:
        item["category"] = category_for(str(item["path"]))
    total_bytes = sum(int(item["size"]) for item in files)
    snapshot_digest = hashlib.sha256(
        "\n".join(f"{item['path']}:{item['sha256']}" for item in files).encode("utf-8")
    ).hexdigest()
    payload = {
        "title": "农场：无限 / PvZ Infinite 项目总档案",
        "conceptVersion": CONCEPT_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fileCount": len(files),
        "totalBytes": total_bytes,
        "snapshotSha256": snapshot_digest,
        "modelViewerVersion": MODEL_VIEWER_VERSION,
        "files": files,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    document = (
        HTML_TEMPLATE.replace("__PAYLOAD__", payload_json)
        .replace("__MODEL_VIEWER_URL__", MODEL_VIEWER_URL)
        .replace("__MODEL_VIEWER_VERSION__", MODEL_VIEWER_VERSION)
    )
    output.write_text(document, encoding="utf-8", newline="\n")
    print(
        f"Built {output.relative_to(root)} with {len(files)} files and "
        f"{total_bytes} source bytes; wrote {index_name}."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Repository root; defaults to script parent parent")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output HTML path relative to root")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="Pages index path relative to root")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    build_html(root, output, args.index)


if __name__ == "__main__":
    main()
