from __future__ import annotations
import json, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from .storage import connect, init, rights_case_report


def _rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def dashboard_html() -> bytes:
    return """<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Author.Today Intelligence</title><style>
:root{--bg:#f4f1eb;--ink:#20211f;--muted:#6d7069;--line:#d7d2c8;--accent:#9c5f2d;--paper:#fff;--ok:#426a50}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}header{padding:28px 5vw 18px;border-bottom:1px solid var(--line);background:var(--paper)}h1{font:34px Georgia,serif;margin:0 0 6px}main{max-width:1180px;margin:auto;padding:28px 5vw}.notice{border-left:3px solid var(--accent);padding:12px 16px;background:#fff8ef;margin-bottom:24px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card,.panel{background:var(--paper);border:1px solid var(--line);padding:18px}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.num{font:30px Georgia,serif;margin-top:5px}.panel{margin-top:18px}table{width:100%;border-collapse:collapse;background:var(--paper);margin-top:10px}th,td{text-align:left;vertical-align:top;padding:11px;border-bottom:1px solid var(--line)}th{font-size:12px;color:var(--muted)}button,select{background:var(--ink);color:white;border:0;padding:9px 13px;cursor:pointer}.tag{background:#eee8df;color:var(--ink);margin:2px}.source,code{font-family:ui-monospace,monospace;font-size:12px;color:var(--muted)}a{color:var(--accent)}svg{width:100%;height:220px;background:#fbfaf7;border:1px solid var(--line)}.fact{color:var(--ok);font-weight:700}.empty{color:var(--muted);padding:18px 0}@media(max-width:760px){.grid{grid-template-columns:1fr}th:nth-child(3),td:nth-child(3){display:none}}
</style><header><h1>Author.Today Intelligence</h1><div>Локальные данные, проверяемые источники, никаких догадок без доказательств.</div></header><main>
<div class='notice'><b>Приватная автоматизация отключена.</b> Официальная оферта запрещает скриптовый сбор. Приватные отчёты импортируются вручную; cookies и пароль не принимаются.</div>
<div class='grid' id='summary'></div>
<section class='panel'><h2>История книги</h2><select id='workSelect'></select><div id='formula' class='source'></div><svg id='chart' viewBox='0 0 900 220' preserveAspectRatio='none'></svg><table><thead><tr><th>Время</th><th>Просмотры</th><th>Лайки</th><th>Источник</th></tr></thead><tbody id='points'></tbody></table></section>
<section class='panel'><h2>Книги и последние снимки</h2><table><thead><tr><th>Книга</th><th>Просмотры</th><th>Лайки</th><th>Источник / время</th></tr></thead><tbody id='works'></tbody></table></section>
<section class='panel'><h2>Архивные доказательства</h2><table><thead><tr><th>Источник</th><th>Цель</th><th>Время</th><th>Locator</th></tr></thead><tbody id='archives'></tbody></table></section>
<section class='panel'><h2>Мониторинг прав</h2><p class='source'>Техническое совпадение не устанавливает нарушение. Статус likely_infringement допустим только после ручной проверки.</p><table><thead><tr><th>Произведение</th><th>Кандидат</th><th>Квалификация</th><th>Проверка</th></tr></thead><tbody id='rights'></tbody></table></section>
<section class='panel'><h2>Темы комментариев</h2><p class='source'>Нажмите на тег, чтобы увидеть доказательства, полный комментарий и оригинал.</p><div id='tags'></div><div id='comments'></div></section>
<script>
const esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
const get=u=>fetch(u).then(r=>r.json());
function renderChart(rows){points.innerHTML=rows.map(x=>`<tr><td>${esc(x.captured_at)}</td><td>${esc(x.views)}</td><td>${esc(x.likes)}</td><td><code>${esc(x.source_class)}<br>${esc(x.source_url)}</code></td></tr>`).join('');if(!rows.length){chart.innerHTML='';formula.textContent='Нет снимков';return}let vals=rows.map(x=>Number(x.views||0)),min=Math.min(...vals),max=Math.max(...vals),span=Math.max(1,max-min),xy=vals.map((v,i)=>`${20+i*(860/Math.max(1,vals.length-1))},${200-(v-min)*170/span}`).join(' ');chart.innerHTML=`<polyline fill='none' stroke='#9c5f2d' stroke-width='4' points='${xy}'/>`+vals.map((v,i)=>`<circle cx='${20+i*(860/Math.max(1,vals.length-1))}' cy='${200-(v-min)*170/span}' r='5' fill='#20211f'/>`).join('');formula.innerHTML=rows.length<2?'Нужны минимум два снимка для изменения.':`<span class=fact>Факт:</span> ${vals.at(-1)} − ${vals[0]} = <b>${vals.at(-1)-vals[0]}</b>. Формула использует показанные ниже сырые точки.`}
function loadWork(id){get('/api/work/'+id+'/snapshots').then(renderChart)}
function loadComments(tag=''){get('/api/comments'+(tag?'?tag='+encodeURIComponent(tag):'')).then(rows=>{comments.innerHTML=rows.length?`<table><thead><tr><th>Подмечание</th><th>Полный комментарий</th><th>Профиль / оригинал</th></tr></thead><tbody>${rows.map(x=>`<tr><td><b>${esc(x.taxonomy_path||'Без тега')}</b><br>${esc(x.stance||'')}<br><q>${esc(x.evidence_excerpt||'')}</q><br><span class=source>уверенность ${esc(x.confidence)} · ${esc(x.derivation)} · confirmed=${esc(x.confirmed)}</span></td><td>${esc(x.body)}</td><td><a href='${esc(x.profile_url)}' target='_blank'>профиль</a><br><a href='${esc(x.source_url)}' target='_blank'>оригинал</a><br><span class=source>${esc(x.chapter_ref||'книга целиком')}</span></td></tr>`).join('')}</tbody></table>`:`<div class=empty>Нет комментариев для выбранного тега.</div>`})}
Promise.all(['/api/summary','/api/works','/api/archives','/api/tags','/api/rights/cases'].map(get)).then(([s,w,a,t,r])=>{summary.innerHTML=Object.entries(s).map(([k,v])=>`<div class=card><div class=label>${esc(k)}</div><div class=num>${esc(v)}</div></div>`).join('');works.innerHTML=w.map(x=>`<tr><td><b>${esc(x.title)}</b><br><a class=source href='${esc(x.url)}'>${esc(x.url)}</a></td><td>${esc(x.views)}</td><td>${esc(x.likes)}</td><td><code>${esc(x.source_class)}<br>${esc(x.captured_at)}</code></td></tr>`).join('');workSelect.innerHTML=w.map(x=>`<option value='${esc(x.work_id)}'>${esc(x.title)}</option>`).join('');if(w.length)loadWork(w[0].work_id);archives.innerHTML=a.map(x=>`<tr><td>${esc(x.source_class)}</td><td>${esc(x.target_url)}</td><td>${esc(x.captured_at)}</td><td><button class=tag data-locator='${esc(x.locator_json)}'>Показать</button></td></tr>`).join('');rights.innerHTML=r.map(x=>`<tr><td>${esc(x.work_title)}</td><td><a href='${esc(x.source_url)}' target='_blank'>${esc(x.candidate_id||x.source_url)}</a></td><td>${esc(x.qualification)}<br><span class=source>${esc(x.qualification_reason)}</span></td><td>human=${esc(x.reviewed_by_human)}<br>legal=${esc(x.legal_review_status)}</td></tr>`).join('')||'<tr><td colspan=4 class=empty>Кейсы ещё не импортированы.</td></tr>';tags.innerHTML=t.map(x=>`<button class=tag data-tag='${esc(x.taxonomy_path)}'>${esc(x.taxonomy_path)} · ${esc(x.stance)} · ${esc(x.count)}</button>`).join('')||'<div class=empty>Нет импортированных тегов.</div>';document.querySelectorAll('[data-tag]').forEach(b=>b.onclick=()=>loadComments(b.dataset.tag));document.querySelectorAll('[data-locator]').forEach(b=>b.onclick=()=>alert(b.dataset.locator));loadComments()});workSelect.onchange=()=>loadWork(workSelect.value);
</script></main></html>""".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "ATIntel/0.2"
    def log_message(self, fmt, *args): print("http", self.address_string(), fmt % args)
    def _json(self, value, status=200):
        raw=json.dumps(value,ensure_ascii=False).encode(); self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=="/":
            raw=dashboard_html(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(raw)))
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'none'"); self.end_headers(); self.wfile.write(raw); return
        db=connect(self.server.db_path); init(db)
        if parsed.path=="/api/health": return self._json({"status":"ok","private_browser_automation":"disabled_by_platform_terms"})
        if parsed.path=="/api/summary": return self._json({"works":db.execute("SELECT COUNT(*) FROM works").fetchone()[0],"snapshots":db.execute("SELECT COUNT(*) FROM work_snapshots").fetchone()[0],"rights candidates":db.execute("SELECT COUNT(*) FROM rights_candidates").fetchone()[0],"rights cases":db.execute("SELECT COUNT(*) FROM rights_cases").fetchone()[0],"archive captures":db.execute("SELECT COUNT(*) FROM archive_captures").fetchone()[0],"comments":db.execute("SELECT COUNT(*) FROM comments").fetchone()[0],"confirmed tags":db.execute("SELECT COUNT(*) FROM comment_tags WHERE confirmed=1").fetchone()[0],"hypotheses":"0 (not generated)"})
        if parsed.path=="/api/works": return self._json(_rows(db,"""SELECT w.work_id,w.title,w.url,s.views,s.likes,s.comments,s.captured_at,COALESCE(src.source_class,'unknown') source_class FROM works w LEFT JOIN work_snapshots s ON s.work_id=w.work_id AND s.captured_at=(SELECT MAX(s2.captured_at) FROM work_snapshots s2 WHERE s2.work_id=w.work_id) LEFT JOIN sources src ON src.source_id=s.source_id ORDER BY COALESCE(s.views,-1) DESC"""))
        match=re.fullmatch(r"/api/work/(\d+)/snapshots",parsed.path)
        if match: return self._json(_rows(db,"""SELECT s.captured_at,s.views,s.likes,s.comments,COALESCE(src.source_class,'unknown') source_class,COALESCE(src.source_url,'') source_url FROM work_snapshots s LEFT JOIN sources src USING(source_id) WHERE s.work_id=? ORDER BY s.captured_at""",(int(match.group(1)),)))
        if parsed.path=="/api/archives": return self._json(_rows(db,"SELECT source_class,target_url,captured_at,archive_url,digest,locator_json FROM archive_captures ORDER BY captured_at DESC LIMIT 100"))
        if parsed.path=="/api/rights/candidates": return self._json(_rows(db,"SELECT candidate_id,work_id,source_url,observed_at,page_title,access_status,capture_sha256,license_status FROM rights_candidates ORDER BY observed_at DESC"))
        if parsed.path=="/api/rights/cases": return self._json(_rows(db,"SELECT case_id,work_id,candidate_id,work_title,rights_holder,source_url,captured_at,qualification,qualification_reason,reviewed_by_human,legal_review_status FROM rights_cases ORDER BY captured_at DESC"))
        rights_match=re.fullmatch(r"/api/rights/cases/([^/]+)",parsed.path)
        if rights_match:
            try: return self._json(rights_case_report(db,rights_match.group(1)))
            except KeyError: return self._json({"error":"not found"},404)
        if parsed.path=="/api/tags": return self._json(_rows(db,"SELECT taxonomy_path,stance,COUNT(*) count,ROUND(AVG(confidence),2) avg_confidence FROM comment_tags GROUP BY taxonomy_path,stance ORDER BY count DESC"))
        if parsed.path=="/api/profiles": return self._json(_rows(db,"""SELECT c.profile_url,MAX(c.display_name) display_name,COUNT(DISTINCT c.comment_id) comment_count,COUNT(DISTINCT c.work_id) work_count,MIN(c.published_at) first_seen,MAX(c.published_at) last_seen,GROUP_CONCAT(DISTINCT t.taxonomy_path) observed_topics FROM comments c LEFT JOIN comment_tags t USING(comment_id) WHERE c.profile_url IS NOT NULL GROUP BY c.profile_url ORDER BY comment_count DESC LIMIT 200"""))
        if parsed.path=="/api/comments":
            tag=parse_qs(parsed.query).get("tag",[None])[0]
            sql="""SELECT c.comment_id,c.work_id,c.chapter_ref,c.profile_url,c.body,c.source_url,c.published_at,t.taxonomy_path,t.stance,t.evidence_excerpt,t.confidence,t.derivation,t.confirmed FROM comments c LEFT JOIN comment_tags t USING(comment_id)"""
            return self._json(_rows(db,sql+(" WHERE t.taxonomy_path=?" if tag else "")+" ORDER BY c.published_at DESC LIMIT 200",(tag,) if tag else ()))
        match=re.fullmatch(r"/api/comments/([^/]+)",parsed.path)
        if match:
            row=db.execute("SELECT * FROM comments WHERE comment_id=?",(match.group(1),)).fetchone()
            if not row:return self._json({"error":"not found"},404)
            value=dict(row);value["tags"]=_rows(db,"SELECT taxonomy_path,stance,evidence_excerpt,confidence,derivation,confirmed FROM comment_tags WHERE comment_id=?",(match.group(1),));return self._json(value)
        return self._json({"error":"not found"},404)
    def do_POST(self): return self._json({"error":"API is read-only; use local CLI for public collection and user-selected manual imports"},405)


def serve(db_path:str,host:str="127.0.0.1",port:int=8787):
    server=ThreadingHTTPServer((host,port),Handler);server.db_path=db_path
    print(f"Serving evidence UI on http://{host}:{port}");server.serve_forever()
