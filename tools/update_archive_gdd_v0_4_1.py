#!/usr/bin/env python3
"""Update the HTML archive builder for professional Master GDD browsing.

Adds Master GDD as the default document, quick-access buttons, a generated
chapter table of contents, stable heading anchors, and Markdown table support.
The migration is idempotent and runs before the archive is rebuilt.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/build_archive.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Missing archive builder anchor for {label}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    if replacement.strip() in text:
        return text
    a = text.find(start)
    b = text.find(end, a + len(start))
    if a < 0 or b < 0:
        raise RuntimeError(f"Missing archive builder range for {label}")
    return text[:a] + replacement.rstrip() + "\n" + text[b:]


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = text.replace('CONCEPT_VERSION = "Concept v0.4.0"', 'CONCEPT_VERSION = "Concept v0.4.1"', 1)

    text = replace_once(
        text,
        ".binary-card{padding:40px;text-align:center;color:var(--muted)}.integrity{margin-top:18px;padding:14px;border:1px dashed var(--line);border-radius:13px;color:var(--muted);font-size:12px;word-break:break-all}.empty{padding:70px;text-align:center;color:var(--muted)}.error{padding:18px;border:1px solid rgba(255,159,91,.4);border-radius:14px;background:rgba(255,159,91,.08);color:#ffd1ae}.footer{text-align:center;color:#6d8d7f;padding:30px 0}",
        ".binary-card{padding:40px;text-align:center;color:var(--muted)}.gdd-toc{max-width:1080px;margin:0 auto 18px;padding:18px 20px;border:1px solid rgba(111,231,237,.22);border-radius:16px;background:linear-gradient(145deg,rgba(111,231,237,.08),rgba(118,242,167,.04))}.gdd-toc strong{display:block;color:var(--green);margin-bottom:8px}.gdd-toc ol{columns:2;column-gap:34px;margin:0;padding-left:22px}.gdd-toc li{break-inside:avoid;margin:4px 0}.gdd-toc a{color:#c9f7dd;text-decoration:none}.gdd-toc a:hover{color:var(--cyan);text-decoration:underline}.binary-card{padding:40px;text-align:center;color:var(--muted)}.integrity{margin-top:18px;padding:14px;border:1px dashed var(--line);border-radius:13px;color:var(--muted);font-size:12px;word-break:break-all}.empty{padding:70px;text-align:center;color:var(--muted)}.error{padding:18px;border:1px solid rgba(255,159,91,.4);border-radius:14px;background:rgba(255,159,91,.08);color:#ffd1ae}.footer{text-align:center;color:#6d8d7f;padding:30px 0}",
        "Master GDD toc styles",
    )
    text = text.replace(
        "@media(max-width:900px){.shell{display:block}",
        "@media(max-width:900px){.gdd-toc ol{columns:1}.shell{display:block}",
        1,
    )

    text = replace_once(
        text,
        '<div class="actions"><button class="btn" id="copyBtn">复制</button><button class="btn" id="downloadBtn">导出文件</button><button class="btn" id="exportEditsBtn">导出本地修改</button></div>',
        '<div class="actions"><button class="btn" id="masterBtn">主游戏设计</button><button class="btn" id="rulesBtn">AI规则</button><button class="btn" id="copyBtn">复制</button><button class="btn" id="downloadBtn">导出文件</button><button class="btn" id="exportEditsBtn">导出本地修改</button></div>',
        "quick access buttons",
    )
    text = text.replace(
        "<p>无损嵌入主设计、AI规则、逐轮对话、版本历史、代码和资产；支持文本、图片、音频、视频、PDF以及GLB/GLTF模型原位交互预览。</p>",
        "<p>默认打开唯一权威Master GDD，集中浏览已确认、待验证、待定、弃用与范围边界；同时无损嵌入AI规则、逐轮对话、版本历史、代码和全部资产。</p>",
        1,
    )

    insert_marker = "function inline(s){let x=esc(s);x=x.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\\*\\*([^*]+)\\*\\*/g,'<strong>$1</strong>').replace(/\\*([^*]+)\\*/g,'<em>$1</em>').replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href=\"$2\" target=\"_blank\" rel=\"noopener\">$1</a>');return x}\n"
    helpers = r'''function inline(s){let x=esc(s);x=x.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');return x}
function slug(s){return String(s).replace(/`/g,'').replace(/\*+/g,'').trim().toLowerCase().replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu,'-').replace(/^-+|-+$/g,'')||'section'}
function tocFor(src){const seen=new Map(),items=[];for(const line of src.replace(/\r\n/g,'\n').split('\n')){const m=line.match(/^(#{2,3})\s+(.*)$/);if(!m)continue;const title=m[2].replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*`]/g,'').trim();let id=slug(title),n=(seen.get(id)||0)+1;seen.set(id,n);if(n>1)id+='-'+n;items.push({level:m[1].length,title,id})}if(!items.length)return'';return '<nav class="gdd-toc"><strong>Master GDD 章节目录</strong><ol>'+items.map(i=>`<li style="margin-left:${(i.level-2)*16}px"><a href="#${i.id}">${esc(i.title)}</a></li>`).join('')+'</ol></nav>'}
'''
    text = replace_once(text, insert_marker, helpers, "slug and toc helpers")

    new_md = r'''function md(src){
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
'''
    text = replace_between(text, "function md(src){", "function extOf(f)", new_md, "Markdown renderer")

    old_render = "else if(f.text){if(['md','markdown'].includes(ext))v.innerHTML='<article class=\"markdown\">'+md(source)+'</article>'+integrity(f);"
    fixed_render = "else if(f.text){if(['md','markdown'].includes(ext)){const toc=f.path==='docs/design/00-master-game-concept.md'?tocFor(source):'';v.innerHTML=toc+'<article class=\"markdown\">'+md(source)+'</article>'+integrity(f)}else if(['html','htm','svg'].includes(ext))"
    broken_render = "else if(f.text){if(['md','markdown'].includes(ext)){const toc=f.path==='docs/design/00-master-game-concept.md'?tocFor(source):'';v.innerHTML=toc+'<article class=\"markdown\">'+md(source)+'</article>'+integrity(f)};else if(['html','htm','svg'].includes(ext))"
    if broken_render in text:
        text = text.replace(broken_render, fixed_render, 1)
    elif fixed_render not in text:
        replacement = "else if(f.text){if(['md','markdown'].includes(ext)){const toc=f.path==='docs/design/00-master-game-concept.md'?tocFor(source):'';v.innerHTML=toc+'<article class=\"markdown\">'+md(source)+'</article>'+integrity(f)}"
        text = replace_once(text, old_render, replacement, "Master GDD table of contents rendering")

    action_anchor = "$('#search').oninput=e=>{query=e.target.value.trim();renderList()};$$('.tab').forEach(t=>t.onclick=()=>setTab(t.dataset.tab));\n"
    action_new = action_anchor + "$('#masterBtn').onclick=()=>openFile(archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md'));$('#rulesBtn').onclick=()=>openFile(archive.files.find(f=>f.path==='AGENTS.md'));\n"
    text = replace_once(text, action_anchor, action_new, "quick access handlers")

    text = text.replace(
        "openFile(archive.files.find(f=>f.path==='AGENTS.md')||archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md')||archive.files[0]);",
        "openFile(archive.files.find(f=>f.path==='docs/design/00-master-game-concept.md')||archive.files.find(f=>f.path==='AGENTS.md')||archive.files[0]);",
        1,
    )

    PATH.write_text(text, encoding="utf-8", newline="\n")
    print("Updated archive builder for Master GDD browsing.")


if __name__ == "__main__":
    main()
