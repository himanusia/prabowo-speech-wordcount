#!/usr/bin/env python3
"""Build the single-file terminal-style dashboard for one corpus profile."""

from __future__ import annotations

import argparse
import json

from corpus import Corpus, add_profile_argument, load_profile

TEMPLATE = r"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ / corpus index</title>
<style>
:root{--bg:#090d0b;--panel:#0e1611;--panel2:#121e15;--ink:#d9f4df;--muted:#7d9985;--dim:#4e6956;--line:#21372a;--strong:#365641;--green:#91ffae;--green2:#4cb875;--amber:#e5c77d;--mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono",monospace}
*{box-sizing:border-box}html{background:var(--bg);color-scheme:dark}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.5 var(--mono);-webkit-font-smoothing:antialiased}button,input,select{font:inherit}
.shell{width:min(1180px,calc(100% - 32px));margin:auto;padding:18px 0 34px}
.top,.foot{display:flex;justify-content:space-between;gap:16px;align-items:center;color:var(--muted);font-size:11px}.top{padding-bottom:13px;border-bottom:1px solid var(--line)}
.dim{color:var(--dim)}.green{color:var(--green)}.ok:before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--green2);margin:0 7px 1px 0}
.overview{display:grid;grid-template-columns:minmax(0,1fr) minmax(420px,1.05fr);gap:30px;padding:32px 0 26px;border-bottom:1px solid var(--line)}
.eyebrow{color:var(--green2);font-size:10px;letter-spacing:.08em;margin-bottom:10px}
h1{font-size:clamp(24px,3.4vw,37px);line-height:1.04;letter-spacing:-.07em;font-weight:600;margin:0}
.lede{max-width:560px;color:var(--muted);font-size:11px;margin:15px 0 0}
.metrics{display:grid;grid-template-columns:repeat(2,1fr);align-self:end;border-top:1px solid var(--line);border-left:1px solid var(--line)}
.metric{min-height:78px;padding:12px 14px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.metric label{display:block;color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.1em}
.metric b{display:block;font-size:24px;line-height:1;margin-top:9px;font-weight:500;letter-spacing:-.06em}
.metric:first-child b{color:var(--green)}.metric small{display:block;color:var(--dim);font-size:9px;margin-top:8px}
.toolbar{display:flex;align-items:center;flex-wrap:wrap;gap:8px 16px;min-height:62px;border-bottom:1px solid var(--line)}
.control{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:10px}.control label{color:var(--dim)}
input,select{min-height:33px;border:1px solid var(--strong);border-radius:2px;background:var(--panel);color:var(--ink);padding:7px 9px;outline:none}
input{width:min(260px,60vw)}input::placeholder{color:var(--dim)}input:focus,select:focus{border-color:var(--green2);box-shadow:0 0 0 2px #4cb8751a}
.toggle{min-height:33px;padding:0 10px;border:1px solid var(--line);background:transparent;color:var(--muted);cursor:pointer}
.toggle:hover,.toggle.active{border-color:var(--green2);color:var(--green)}
.scope-note{margin-left:auto;color:var(--dim);font-size:10px}
.grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(330px,.9fr);gap:30px;padding-top:26px}
.head{display:flex;justify-content:space-between;align-items:baseline;min-height:34px;border-bottom:1px solid var(--strong)}
h2{font-size:12px;font-weight:600;margin:0}.head span{color:var(--dim);font-size:9px}
.sub{color:var(--muted);font-size:10px;margin:8px 0 13px}
.wordhead,.wordrow{display:grid;grid-template-columns:30px minmax(80px,1fr) minmax(80px,1.5fr) 54px 54px;gap:10px;align-items:center}
.wordhead{min-height:29px;border-bottom:1px solid var(--line);color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.08em}
.wordrow{width:100%;min-height:38px;border:0;border-bottom:1px solid #21372ab3;background:transparent;color:var(--ink);text-align:left;cursor:pointer}
.wordrow:hover,.wordrow.selected{background:var(--panel2)}.wordrow.selected .word{color:var(--green)}
.rank,.count,.coverage{color:var(--muted);font-size:10px}
.word{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.meter{height:7px;background:#17261b;overflow:hidden}.meter i{display:block;height:100%;min-width:2px;background:var(--green2)}
.wordrow.selected .meter i{background:var(--green)}
.detail{margin-top:24px;padding-top:14px;border-top:1px solid var(--strong)}
.detailtitle{display:flex;align-items:baseline;gap:12px}.detailword{color:var(--green);font-size:20px;letter-spacing:-.06em}.detailtitle small{color:var(--muted);font-size:10px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:14px 0}
.stat{padding:8px 9px;background:var(--panel);border:1px solid var(--line)}.stat b{display:block;font-size:15px;font-weight:500}
.stat small{color:var(--dim);font-size:8px;text-transform:uppercase;letter-spacing:.08em}
.break{border-top:1px solid var(--line);max-height:280px;overflow:auto}
.breakrow{display:grid;grid-template-columns:1fr 46px;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);color:var(--muted);font-size:9px}
.breakrow strong{color:var(--ink);font-weight:500}.breakrow span:last-child{text-align:right;color:var(--green)}
table{width:100%;border-collapse:collapse;font-size:10px}
th,td{text-align:left;padding:7px 6px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-size:9px;text-transform:uppercase;letter-spacing:.08em;font-weight:400}
td.num,th.num{text-align:right;color:var(--muted)}
.bartrack{height:6px;background:#17261b;min-width:60px}.bartrack i{display:block;height:100%;background:var(--green2)}
.topicname{color:var(--ink)}
.events{max-height:420px;overflow:auto}
.event{display:grid;grid-template-columns:1fr auto;gap:3px 10px;padding:10px 0;border-bottom:1px solid var(--line);cursor:pointer}
.event:hover,.event.active{background:var(--panel2)}
.event-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:10px}
.event-meta{color:var(--muted);font-size:9px}
.tag{color:var(--amber)}
.signalrow{display:grid;grid-template-columns:78px 1fr 40px;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);font-size:9px;color:var(--muted)}
.signalrow b{color:var(--ink);font-weight:500}
details{margin-top:22px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
summary{padding:11px 0;color:var(--muted);cursor:pointer;font-size:9px;list-style:none}
summary::-webkit-details-marker{display:none}summary:before{content:"[+] ";color:var(--green2)}details[open] summary:before{content:"[-] "}
.method{max-width:900px;padding:0 0 13px;color:var(--muted);font-size:9px}
.method code,.method a{color:var(--green2)}
.foot{padding-top:15px;font-size:9px}.foot a{color:var(--green2);text-decoration:none}
.empty{padding:20px 0;color:var(--dim)}
@media(max-width:900px){.overview,.grid{grid-template-columns:1fr}.scope-note{width:100%;margin-left:0}}
@media(max-width:560px){.shell{width:calc(100% - 20px)}.wordhead,.wordrow{grid-template-columns:24px minmax(70px,1fr) 1fr 44px;gap:7px}.wordhead>:last-child,.wordrow>:last-child{display:none}.metrics{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div><span class="dim">~/research/</span><span class="green">__SLUG__</span><span class="dim"> $ ./index</span></div><div class="ok green" id="stamp">dataset loaded</div></header>
<main>
<section class="overview"><div><div class="eyebrow">// YOUTUBE CAPTIONS · __LANG__ · DEDUPLICATED EVENTS</div><h1>__TITLE__<br>/ corpus index</h1><p class="lede">__LEDE__</p></div><div class="metrics">
<div class="metric"><label>speech events</label><b id="mEvents">—</b><small>unik, sudah dedup</small></div>
<div class="metric"><label>uploads fetched</label><b id="mUploads">—</b><small>caption berhasil diambil</small></div>
<div class="metric"><label>tokens</label><b id="mTokens">—</b><small>event kanonik</small></div>
<div class="metric"><label>vocabulary</label><b id="mUnique">—</b><small>surface forms</small></div>
</div></section>
<section class="toolbar">
<div class="control"><label for="scope">scope</label><select id="scope"><option value="all">semua event</option></select></div>
<div class="control"><label for="search">find</label><input id="search" type="search" placeholder="cari kata  /" autocomplete="off"></div>
<button class="toggle" id="lexical" type="button" aria-pressed="false">sembunyikan kata umum</button>
<span class="scope-note" id="scopeNote">semua event · repeated words retained</span>
</section>
<section class="grid">
<section>
<div class="head"><h2>kata</h2><span id="wordMeta">—</span></div>
<p class="sub">klik kata untuk lihat distribusi antar-event.</p>
<div class="wordhead"><span>#</span><span>kata</span><span>relatif</span><span>count</span><span>event</span></div>
<div id="words"></div>
<div class="detail"><div class="detailtitle"><span class="detailword" id="dWord">—</span><small id="dCount">pilih kata</small></div>
<div class="stats"><div class="stat"><b id="dRate">—</b><small>per 1.000 token</small></div><div class="stat"><b id="dCoverage">—</b><small>event coverage</small></div><div class="stat"><b id="dRank">—</b><small>rank</small></div></div>
<div class="break" id="breakdown"></div></div>
</section>
<aside>
<div class="head"><h2>topik</h2><span>lexical signals</span></div>
<table><thead><tr><th>topik</th><th class="num">/1k</th><th>event</th><th class="num">n</th></tr></thead><tbody id="topics"></tbody></table>
<div class="head" style="margin-top:22px"><h2 id="signalHead">__SIGNAL__</h2><span id="signalMeta">—</span></div>
<p class="sub" id="signalSub">—</p>
<div id="signals"></div>
<div class="head" style="margin-top:22px"><h2>framing</h2><span>pronomina</span></div>
<table><thead><tr><th>kata</th><th class="num">/1k</th><th class="num">count</th><th class="num">event</th></tr></thead><tbody id="framing"></tbody></table>
<div class="head" style="margin-top:22px"><h2>event</h2><span id="eventMeta">—</span></div>
<p class="sub">klik event untuk isolasi hitungan.</p>
<div class="events" id="events"></div>
</aside>
</section>
<details><summary>method + provenance</summary><div class="method">
<p id="methodText"></p>
<p>Sumber caption: <a href="https://github.com/jdepoix/youtube-transcript-api" target="_blank" rel="noreferrer">youtube-transcript-api</a> — caption API, dan panel transcript YouTube kalau API-nya kena rate limit. Dedup event memakai containment shingle, satu sumber kanonik per event. Caption bukan ground truth audio; verifikasi kutipan ke video sebelum publikasi.</p>
</div></details>
</main>
<footer class="foot"><span><span class="dim">/</span> cari · <span class="dim">esc</span> reset</span><span id="repoLink"></span></footer>
</div>
<script>
const DATA=__DATA__;
const STOP=new Set(DATA.method_stopwords);
const SIGNAL=DATA.policy_signal_label;
const state={scope:'all',query:'',lexical:false,word:null};
const $=id=>document.getElementById(id);
const fmt=n=>new Intl.NumberFormat('id-ID').format(n);
const events=[...DATA.sources].sort((a,b)=>b.date.localeCompare(a.date));
const scopeEvents=()=>state.scope==='all'?DATA.sources:DATA.sources.filter(s=>s.duplicate_group===state.scope);
function rows(){
  const active=scopeEvents();
  if(state.scope==='all'){
    return DATA.word_index.map(([word,count,speechCount])=>({word,count,speechCount}));
  }
  const source=active[0];
  if(!source)return [];
  const total=Object.entries(source.counts);
  return total.map(([word,count])=>({word,count,speechCount:count>0?1:0})).sort((a,b)=>b.count-a.count||a.word.localeCompare(b.word));
}
function metrics(){
  const ss=scopeEvents();
  $('mEvents').textContent=fmt(DATA.totals.unique_speech_events);
  $('mUploads').textContent=fmt(DATA.totals.eligible_caption_items);
  $('mTokens').textContent=fmt(DATA.totals.total_tokens);
  $('mUnique').textContent=fmt(DATA.totals.unique_words);
  $('scopeNote').textContent=state.scope==='all'
    ? fmt(DATA.totals.duplicate_items_removed)+' upload duplikat dibuang · '+fmt(ss.length)+' event'
    : 'satu event · '+fmt(ss[0]?ss[0].token_count:0)+' token';
  $('stamp').textContent='generated '+DATA.generated_at.slice(0,10);
}
function scopeOptions(){
  const el=$('scope'),current=state.scope;
  el.innerHTML='<option value="all">semua event ('+DATA.sources.length+')</option>';
  for(const s of events){const o=document.createElement('option');o.value=s.duplicate_group;o.textContent=s.date+' · '+s.title.slice(0,64);el.append(o)}
  el.value=current;
}
function detail(all){
  const x=all.find(r=>r.word===state.word)||all[0];
  if(!x){$('dWord').textContent='—';$('dCount').textContent='pilih kata';$('breakdown').innerHTML='';return}
  state.word=x.word;
  const total=all.reduce((n,r)=>n+r.count,0);
  const rank=all.findIndex(r=>r.word===x.word)+1;
  $('dWord').textContent=x.word;
  $('dCount').textContent=fmt(x.count)+' kemunculan';
  $('dRate').textContent=total?(x.count/total*1000).toFixed(2):'0';
  $('dCoverage').textContent=x.speechCount+'/'+scopeEvents().length;
  $('dRank').textContent='#'+rank;
  $('breakdown').innerHTML=scopeEvents()
    .map(s=>({s,count:s.counts[x.word]||0}))
    .sort((a,b)=>b.count-a.count)
    .map(r=>'<div class="breakrow"><span><strong>'+r.s.date+'</strong> · '+r.s.channel+'</span><span>'+fmt(r.count)+'</span></div>').join('');
}
function words(){
  const all=rows();
  const q=state.query.trim().toLowerCase();
  const filtered=all.filter(r=>!q||r.word.includes(q));
  const shown=filtered.filter(r=>!state.lexical||!STOP.has(r.word)).slice(0,60);
  const max=shown.length?shown[0].count:1;
  $('wordMeta').textContent=fmt(filtered.length)+' kata · '+fmt(all.reduce((n,r)=>n+r.count,0))+' token';
  const el=$('words');el.innerHTML='';
  if(!shown.length){el.innerHTML='<div class="empty">tidak ada kata cocok</div>';detail([]);return}
  if(!state.word||!shown.some(r=>r.word===state.word))state.word=shown[0].word;
  for(const [i,r] of shown.entries()){
    const b=document.createElement('button');
    b.className='wordrow'+(r.word===state.word?' selected':'');
    b.innerHTML='<span class="rank">'+String(i+1).padStart(2,'0')+'</span><span class="word">'+r.word+'</span><span class="meter"><i style="width:'+(r.count/max*100)+'%"></i></span><span class="count">'+fmt(r.count)+'</span><span class="coverage">'+r.speechCount+'/'+scopeEvents().length+'</span>';
    b.onclick=()=>{state.word=r.word;words()};
    el.append(b);
  }
  detail(shown);
}
function topics(){
  const global=DATA.totals.topics;
  const max=Math.max(...global.map(t=>t.per_1000_tokens),1);
  $('topics').innerHTML=global.map(t=>'<tr><td class="topicname">'+t.topic+'</td><td class="num">'+t.per_1000_tokens.toFixed(2)+'</td><td><div class="bartrack"><i style="width:'+(t.per_1000_tokens/max*100)+'%"></i></div></td><td class="num">'+t.speech_count+'</td></tr>').join('');
}
function signals(){
  const hit=events.filter(e=>e.policy_signals.policy_signal_count>0||e.policy_signals.ambiguous_count>0);
  $('signalMeta').textContent=hit.length+'/'+DATA.sources.length+' event';
  $('signals').innerHTML=hit.map(e=>{
    const flags=e.policy_signals.ambiguous_count?' <span class="tag">'+e.policy_signals.ambiguous_count+' ambigu</span>':'';
    return '<div class="signalrow"><span>'+e.date+'</span><span><b>'+e.title.slice(0,52)+'</b>'+flags+'</span><span class="num">'+e.policy_signals.policy_signal_count+'</span></div>';
  }).join('')||'<div class="empty">tidak ada sinyal</div>';
}
function framing(){
  $('framing').innerHTML=DATA.totals.framing.map(f=>'<tr><td class="topicname">'+f.word+'</td><td class="num">'+f.per_1000_tokens.toFixed(2)+'</td><td class="num">'+fmt(f.count)+'</td><td class="num">'+f.speech_count+'</td></tr>').join('');
}
function eventList(){
  $('eventMeta').textContent='satu event per pidato';
  $('events').innerHTML=events.map(e=>'<div class="event'+(state.scope===e.duplicate_group?' active':'')+'" data-g="'+e.duplicate_group+'" tabindex="0" role="button"><div class="event-title">'+e.title+'</div><div class="event-meta">'+e.date+' · '+e.channel+' · '+(e.duplicate_count?'<span class="tag">'+e.duplicate_count+' duplikat</span>':'tanpa duplikat')+'</div><div class="event-meta">'+fmt(e.token_count)+' token · '+e.source_tier+'</div></div>').join('');
  for(const item of $('events').querySelectorAll('.event')){
    const pick=()=>{state.scope=state.scope===item.dataset.g?'all':item.dataset.g;state.word=null;render()};
    item.onclick=pick;
    item.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();pick()}};
  }
}
function method(){
  const m=DATA.method;
  $('methodText').textContent=m.source+'. Metrik utama: '+m.primary_metric+'. Normalisasi: '+m.normalization+'. Dedup: '+m.deduplication+'. Aturan '+SIGNAL+': '+m.policy_signal_rule+'. Peringatan: '+m.warning;
  $('repoLink').innerHTML=DATA.repo_url?'<a href="'+DATA.repo_url+'" target="_blank" rel="noreferrer">'+DATA.repo_label+' ↗</a>':'';
}
function render(){method();scopeOptions();metrics();words();topics();signals();framing();eventList();$('lexical').className='toggle'+(state.lexical?' active':'');$('lexical').setAttribute('aria-pressed',String(state.lexical));}
$('scope').onchange=e=>{state.scope=e.target.value;state.word=null;render()};
$('search').oninput=e=>{state.query=e.target.value;words()};
$('lexical').onclick=()=>{state.lexical=!state.lexical;render()};
document.onkeydown=e=>{if(e.key==='/'&&document.activeElement!==$('search')){e.preventDefault();$('search').focus()}if(e.key==='Escape'){$('search').value='';state.query='';$('scope').value='all';state.scope='all';$('search').blur();render()}};
render();
window.__corpus={events:DATA.totals.unique_speech_events,uploads:DATA.totals.eligible_caption_items,tokens:DATA.totals.total_tokens,unique:DATA.totals.unique_words,wordsShown:()=>$('words').querySelectorAll('.wordrow').length,topicRows:()=>$('topics').querySelectorAll('tr').length,mbgRows:()=>$('signals').querySelectorAll('.signalrow').length,signalRows:()=>$('signals').querySelectorAll('.signalrow').length,eventRows:()=>$('events').querySelectorAll('.event').length};
</script>
</body>
</html>
"""

LEDE = (
    "Setiap pidato dihitung sebagai satu event, walaupun diunggah banyak kanal. "
    "Angka kata, topik, sinyal kebijakan, dan framing dihitung dari event kanonik."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the dashboard for one corpus profile.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    if not corpus.analysis.exists():
        raise SystemExit(f"no analysis at {corpus.analysis}; run scripts/analyze.py first")
    data = json.loads(corpus.analysis.read_text(encoding="utf-8"))

    signal = profile["policy_signals"]
    data["policy_signal_label"] = signal["label"]
    data["method_stopwords"] = profile["stopwords"]
    data["repo_url"] = profile.get("repo_url", "")
    data["repo_label"] = profile.get("repo_label", "")

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = (
        TEMPLATE
        .replace("__DATA__", payload)
        .replace("__TITLE__", profile.get("display_name", profile["name"]))
        .replace("__SLUG__", profile["name"])
        .replace("__LANG__", profile.get("language_code", "").upper())
        .replace("__LEDE__", LEDE)
        .replace("__SIGNAL__", signal["label"].casefold())
    )
    corpus.dashboard.write_text(html, encoding="utf-8")
    print(f"wrote {corpus.dashboard}")
    print(
        f"embedded events={data['totals']['unique_speech_events']} "
        f"uploads={data['totals']['eligible_caption_items']} "
        f"tokens={data['totals']['total_tokens']} words={len(data['word_index'])}"
    )


if __name__ == "__main__":
    main()
