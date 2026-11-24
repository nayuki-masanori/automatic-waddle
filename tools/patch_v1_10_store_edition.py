import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
def rep(old,new,cnt=1):
    global s
    n=s.count(old); assert n==cnt,(n,old[:100]); s=s.replace(old,new)

# ── 0) 自分自身のソース（実行前の状態）を取り込む仕掛け＋原価計算スクリプトに目印 ──
rep("""<script>
/* ═════════ HEART HALO CORE""","""<script id="pvTop">window.__PV_TOP=document.documentElement.outerHTML;document.addEventListener('DOMContentLoaded',()=>{window.__PV_NS=document.scripts.length;});</script>
<script>
/* ═════════ HEART HALO CORE""")
rep("""<script>
/* ═════════ 原価計算（社内用のみ）""","""<script id="hcCost">
/* ═════════ 原価計算（社内用のみ）""")

# ── 1) モード：店舗版は PV_STORE（確定価格表）を持つ ──
rep("const INTERNAL=true;","const INTERNAL=!window.PV_STORE;\nconst APP_VER='1.10.0',APP_DATE='2026.11.24';")

# ── 2) 特別仕様：原価型（社内）と確定額型（本社→店舗、pre＝税抜額）を分けて扱う ──
rep("""function currentQuote(){
  const c=HH.cBracket(S.w),z=isRing()?S.sz:null,F=frameQuote(S.sku,S.metal,c,z),t=taxRate();
  let adjPre=0,adjLbl='',r=F.r;
  if(S.ex.length){const F1=frameQuote(S.sku,S.metal,c,z,S.ex);r=F1.r;if(F1.pre!=null&&F.pre!=null)adjPre=F1.pre-F.pre;adjLbl=exLabel();}""",
"""function exCost(){return S.ex.filter(e=>e.pre==null);}
function exFix(){return S.ex.filter(e=>e.pre!=null);}
function currentQuote(){
  const c=HH.cBracket(S.w),z=isRing()?S.sz:null,F=frameQuote(S.sku,S.metal,c,z),t=taxRate();
  let adjPre=0,adjLbl='',r=F.r;
  const exC=exCost(),fixPre=exFix().reduce((a,e)=>a+(numv(e.pre)||0),0);
  if(exC.length){const F1=frameQuote(S.sku,S.metal,c,z,exC);r=F1.r;if(F1.pre!=null&&F.pre!=null)adjPre=F1.pre-F.pre;}
  adjPre+=fixPre;if(S.ex.length)adjLbl=exLabel();""")
rep("""function costNow(){const c=HH.cBracket(S.w),ring=isRing();return HC.costOf(EST,S.sku,S.metal,c,ring?HC.priceSize(EST,S.sz):null,{extras:S.ex});}""",
"""function costNow(){const c=HH.cBracket(S.w),ring=isRing();return HC.costOf(EST,S.sku,S.metal,c,ring?HC.priceSize(EST,S.sz):null,{extras:exCost()});}
function clearAdj(){if(!confirm('特別仕様（本社指定の加算額）を解除します。よろしいですか？'))return;S.ex=[];saveEx();refreshAll(false);}""")

# ── 3) 店舗版では地金重量（社内）を出さない／価格版を表示 ──
rep("""const G=HC.grams(EST,S.sku,S.metal,c,ring?S.sz:null);rows+=`<tr><td style="color:var(--txt3)">地金重量（目安・社内）</td><td class="n" style="color:var(--txt3)">${f2(G.g)}g</td></tr>`;""",
"""if(INTERNAL){const G=HC.grams(EST,S.sku,S.metal,c,ring?S.sz:null);rows+=`<tr><td style="color:var(--txt3)">地金重量（目安・社内）</td><td class="n" style="color:var(--txt3)">${f2(G.g)}g</td></tr>`;}""")
rep("""<div class="pb-s">${S.metal}　中石 ${q.c.toFixed(1)}mm帯　${isRing()?'#'+S.sz:'チェーン45cm'}""",
"""<div class="pb-s">${S.metal}　中石 ${q.c.toFixed(1)}mm帯　${isRing()?'#'+S.sz:'チェーン45cm'}　<span style="opacity:.75">価格版 ${pvLabel()}</span>""")
rep("""<div><span>有効期限</span>${inp('valid')}</div></div></div></div>""",
"""<div><span>有効期限</span>${inp('valid')}</div><div><span>価格版</span><b style="font-weight:normal">${pvLabel()}</b></div></div></div></div>""")
rep("""function internalQuotePage(){
  const r=costNow()""","""function internalQuotePage(){
  if(!INTERNAL)return '';
  const r=costNow()""")

# ── 4) 見積データ：価格版No を記録。店舗へ送るときは原価情報を含めない ──
rep("""function exportQuoteData(){const q=currentQuote();if(!S.q.no)openQuote();
  try{localStorage.setItem('pv_hh_ex_'+S.q.no,JSON.stringify(S.ex));}catch(e){}
  const D={kind:'PV_HeartHalo_Quote',ver:1,saved:new Date().toISOString(),from:INTERNAL?'HQ':'STORE',
    sel:{sku:S.sku,metal:S.metal,w:S.w,sz:S.sz,center:S.center,cInc:S.cInc,cad:S.cad||'',ex:S.ex},""",
"""function exportQuoteData(){const q=currentQuote();if(!S.q.no)openQuote();
  try{localStorage.setItem('pv_hh_ex_'+S.q.no,JSON.stringify(S.ex));}catch(e){}
  let ex=S.ex,forStore=!INTERNAL;
  if(INTERNAL){forStore=confirm('店舗へ送る見積データとして保存しますか？\\n\\nOK：店舗用（原価情報を含めない。特別仕様は確定額で渡します）\\nキャンセル：社内保存用（追加原価の内訳を含む）');
    if(forStore){if(pvDirty()&&!confirm('原価マスターが店舗版 '+(pvCur()?pvCur().no:'（未発行）')+' から変更されています。\\n店舗の価格と合わない可能性があります（先に「店舗版を発行」を推奨）。\\nこのまま保存しますか？'))return;
      ex=q.adjPre?[{sec:'fix',l:q.adjLbl,pre:q.adjPre}]:[];}}
  const D={kind:'PV_HeartHalo_Quote',ver:2,saved:new Date().toISOString(),from:INTERNAL?'HQ':'STORE',pv:pvNo(),forStore,
    sel:{sku:S.sku,metal:S.metal,w:S.w,sz:S.sz,center:S.center,cInc:S.cInc,cad:S.cad||'',ex},""")
rep("""a.download=`PV_HeartHalo_見積データ_${S.q.no}.json`;""","""a.download=`PV_HeartHalo_見積データ_${S.q.no}${forStore&&INTERNAL?'_店舗用':''}.json`;""")
rep("""  if(Array.isArray(v.ex)){S.ex=v.ex;saveEx();}""","""  if(Array.isArray(v.ex)){S.ex=INTERNAL?v.ex:v.ex.filter(e=>e.pre!=null);
    if(!INTERNAL&&!S.ex.length&&D.price&&D.price.adjPre)S.ex=[{sec:'fix',l:D.price.adjLbl||'特別仕様',pre:D.price.adjPre}];saveEx();}""")
rep("""  const now=currentQuote();let msg='見積データを読み込みました（'+(D.q&&D.q.no||'')+'）';
  if(D.price&&D.price.frameInc!=null&&now.frameInc!==D.price.frameInc)msg+='\\n※ 作成時の枠価格 '+yen(D.price.frameInc)+' → 現在の価格表では '+yen(now.frameInc);""",
"""  const now=currentQuote();let msg='見積データを読み込みました（'+(D.q&&D.q.no||'')+'）';
  const pvOld=D.pv||'（記録なし）',pvNow=pvNo();
  if(pvOld!==pvNow)msg+='\\n\\n価格版が変わっています：作成時 '+pvOld+' → 現在 '+pvNow;
  if(D.price&&D.price.frameInc!=null&&now.frameInc!==D.price.frameInc)msg+='\\n※ 枠価格（税込）'+yen(D.price.frameInc)+' → '+yen(now.frameInc)+'（現在の価格版で再計算しました）';
  if(INTERNAL&&pvOld!==pvNow){const h=pvFind(D.pv);if(h){const c=HH.cBracket(S.w),z=isRing()?HC.priceSize(h.est,S.sz):null;
      const a=HC.costOf(h.est,S.sku,S.metal,c,z),b=costNow();msg+='\\n※ 原価 '+h.no+'：'+fmt(a.cost)+' → 現在：'+fmt(b.cost);}}
  if(!INTERNAL&&D.pv&&pvSeq(D.pv)>pvSeq(pvNow))msg+='\\n\\n⚠ この見積は新しい価格版（'+D.pv+'）で作成されています。本社から最新の店舗用アプリを受け取ってください。';""")

# ── 5) 価格版（バリエーション）管理・店舗版の発行（本社のみ）──
rep("""function toggleQInt(){renderQuote();}""","""function toggleQInt(){renderQuote();}

/* ═════════ 価格版（店舗版の発行）═════════
   店舗版を発行するたびに、その時点の原価マスター（スナップショット）と販売価格表を「価格版 P001…」として確定保存。
   以後マスターを修正しても確定済みの版は変わらない。修正後に再発行すると次の番号になり、店舗の売価が切り替わる。 */
function pvHist(){return INTERNAL?(EST.pvHist||(EST.pvHist=[])):[];}
function pvCur(){const H=pvHist();return H.length?H[H.length-1]:null;}
function pvFind(no){return pvHist().find(h=>h.no===no)||null;}
function pvSeq(no){const m=/P(\\d+)/.exec(no||'');return m?+m[1]:0;}
function pvSig(T){return JSON.stringify({tax:T.tax,sizePrice:T.sizePrice,prices:T.prices});}
function pvDirty(){const c=pvCur();return !c||pvSig(HC.priceTable(EST))!==pvSig(c.table);}
function pvNo(){if(!INTERNAL)return window.PV_STORE.pv;const c=pvCur();return c?(pvDirty()?c.no+'+編集中':c.no):'未発行';}
function pvLabel(){if(!INTERNAL)return PV_STORE.pv+'（'+PV_STORE.issued.slice(0,10)+'）';return pvNo();}
function estSnapshot(){const o=JSON.parse(JSON.stringify(EST));delete o.pvHist;return o;}
function issueStore(){
  const T=HC.priceTable(EST),c=pvCur();
  if(c&&!pvDirty()){if(confirm('原価マスターは店舗版 '+c.no+'（'+c.date.slice(0,10)+' 発行）から変わっていません。\\n同じ '+c.no+' の店舗用アプリを書き出しますか？'))downloadStore(c);return;}
  const no='P'+String((c?pvSeq(c.no):0)+1).padStart(3,'0');
  const note=prompt('店舗版 '+no+' を発行します。\\nこの時点の原価と販売価格を '+no+' として確定し、店舗用アプリ（原価なし）を書き出します。\\n\\n発行メモ（例：地金相場改定 K18 16,500→17,200）',c?'':'初回発行');
  if(note===null)return;
  const h={no,date:new Date().toISOString(),note:note||'',appVer:APP_VER,est:estSnapshot(),table:T};
  pvHist().push(h);saveEst();renderEst(true);downloadStore(h);
}
function pvRedownload(no){const h=pvFind(no);if(h)downloadStore(h);}
function pvSaveSnap(no){const h=pvFind(no);if(!h)return;const a=document.createElement('a');a.download=`PV_HeartHalo_原価マスター_${h.no}.json`;
  a.href=URL.createObjectURL(new Blob([JSON.stringify(Object.assign({},h.est,{pvFrom:h.no}),null,2)],{type:'application/json'}));a.click();}
function storeHCScript(h){
  const meta={pv:h.no,issued:h.date,note:h.note||'',appVer:APP_VER};
  const T={tax:h.table.tax,sizePrice:h.table.sizePrice,prices:h.table.prices};
  const js=x=>JSON.stringify(x).replace(/</g,'\\\\u003c');
  return '<script id="hcCost">\\n/* 店舗用：価格版 '+h.no+'（'+h.date.slice(0,10)+' 本社発行）の確定販売価格（税抜・中石別）のみ。原価データは含みません。 */\\n'+
   'window.PV_STORE='+js(meta)+';\\n'+
   'var HC=(function(){const PT='+js(T)+';\\n'+
   'function num(v){if(v==null||v==="")return null;const n=parseFloat(String(v).replace(/[,，¥￥円\\\\s]/g,""));return isNaN(n)?null:n;}\\n'+
   'function defaults(){return {tax:PT.tax,sizePrice:PT.sizePrice};}\\n'+
   'function priceSize(M,z){if(z==null)return null;if(PT.sizePrice==="each")return z;if(PT.sizePrice==="one")return 20;return z<=13?13:20;}\\n'+
   'function costOf(M,sku,metal,c,z){c=HH.cBracket(c);let v=((PT.prices[sku]||{})[metal]||{})[c];if(v&&typeof v==="object")v=v[z];return {P:v>0?{pre:v}:null,extras:[]};}\\n'+
   'function grams(){return {g:0,k18:0,head:0,shank:0};}\\n'+
   'return {defaults,num,priceSize,costOf,grams};})();\\n</'+'script>';
}
function buildStoreHTML(h){
  const all=[...document.scripts],i0=all.findIndex(x=>x.id==='pvTop'),n=window.__PV_NS||all.length;
  if(i0<0||!window.__PV_TOP)throw new Error('元データを取得できません');
  let top=window.__PV_TOP.replace(/<\\/body>\\s*<\\/html>\\s*$/i,'').replace(/<title>（社内用）/,'<title>（店舗用 '+h.no+'）');
  const out=['<!DOCTYPE html>\\n',top];
  all.slice(i0+1,n).forEach(x=>{if(x.src)return;out.push('\\n',x.id==='hcCost'?storeHCScript(h):x.outerHTML);});
  out.push('\\n</body>\\n</html>\\n');return out.join('');
}
function downloadStore(h){
  try{const html=buildStoreHTML(h);if(/"metals"|labor|setSide|supMargin/.test(html.slice(html.indexOf('id="hcCost"'),html.indexOf('id="hcCost"')+400000).split('</'+'script>')[0]))throw new Error('原価データの除去を確認できませんでした');
    const a=document.createElement('a');a.download=`PonteVecchio_HeartHalo_店舗用_${h.no}.html`;a.href=URL.createObjectURL(new Blob([html],{type:'text/html'}));a.click();}
  catch(e){alert('店舗用アプリを書き出せませんでした：'+e.message);}
}
function pvPanel(){
  const H=pvHist(),c=pvCur(),dirty=pvDirty();
  const smp=t=>{const g=(s,z)=>{let v=((t.prices[s]||{}).K18YG||{})[6];if(v&&typeof v==='object')v=v[z];return v?yen(Math.round(v*(100+t.tax)/100)):'—';};return `NL ${g('NL')}／RA ${g('RA',13)}／RB ${g('RB',13)}`;};
  return `<div class="ec"><h3><span class="no">5</span>店舗版（価格版）の発行<span class="s">店舗用アプリには販売価格のみ・原価なし</span></h3>
   <div class="callout ${c&&!dirty?'ok':'ng'}" style="margin:0 0 8px">${c?(dirty?`⚠ 原価マスターが店舗版 <b>${c.no}</b> から変更されています。店舗の売価は ${c.no} のままです。反映するには「店舗版を発行」してください（次は P${String(pvSeq(c.no)+1).padStart(3,'0')}）。`:`✓ 店舗の現行版 <b>${c.no}</b>（${c.date.slice(0,10)} 発行）とマスターは一致しています。`):'店舗版はまだ発行されていません。'}</div>
   <div class="tools"><div class="row"><button class="cbtn pri" onclick="issueStore()">🏬 店舗版を発行（書き出し）</button></div></div>
   ${H.length?`<table class="et2" style="margin-top:8px"><tr><th>価格版</th><th>発行日</th><th>メモ</th><th>上代例（K18YG 6.0mm #13・税込）</th><th></th></tr>
   ${H.slice().reverse().map(h=>`<tr><td class="c"><b>${h.no}</b>${h===c?'<div class="sub">現行</div>':''}</td><td class="c">${h.date.slice(0,10)}</td><td>${esc(h.note)}</td><td class="n" style="font-size:11px">${smp(h.table)}</td>
     <td class="c" style="white-space:nowrap"><button class="cbtn" onclick="pvRedownload('${h.no}')">店舗版を再出力</button> <button class="cbtn" onclick="pvSaveSnap('${h.no}')">確定原価（JSON）</button></td></tr>`).join('')}</table>`:''}
   <p class="d" style="margin:6px 0 0">発行時点の原価マスターと販売価格を価格版Noごとに確定保存します（後からマスターを直しても確定済みの版は変わりません）。見積データには価格版Noが記録され、読込時に版が違えば原価・売価の差を表示して現在の版で計算し直します。</p></div>`;
}""")
rep("""     <p class="d" style="margin:4px 0 0">店舗用価格表（JSON）には販売価格（本体）のみが入り、原価は含まれません。店舗用アプリの「価格表 更新」から読み込みます。</p></div></div>
  </div>""","""     <p class="d" style="margin:4px 0 0">店舗用価格表（JSON）には販売価格（本体）のみが入り、原価は含まれません。</p></div></div>
   ${pvPanel()}
  </div>""")
# 見積ボード上部にも発行ボタン、ピルに価格版の状態
rep("""      <button class="cbtn" onclick="exportPriceTable()">&#128228; 店舗用価格表</button>""","""      <button class="cbtn pri" onclick="issueStore()">&#127980; 店舗版を発行</button>""")
rep("""pill.innerHTML=q.ready?`✓ 前面ボード：枠 税込 <b>${yen(q.frameInc)}</b>`:'価格を計算できません（原価マスターを確認）';}""",
"""pill.innerHTML=(q.ready?`✓ 前面ボード：枠 税込 <b>${yen(q.frameInc)}</b>`:'価格を計算できません（原価マスターを確認）')+`　｜　店舗版 <b>${pvNo()}</b>${INTERNAL&&pvDirty()?' <span style="color:#A0501A">（未発行の変更あり）</span>':''}`;}""")
# マスター読込で履歴を消さない（読込ファイルに履歴が無ければ現在の履歴を保持）
rep("""function importEst(inp){const f=inp.files&&inp.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{try{mergeEst(JSON.parse(rd.result));""",
"""function importEst(inp){const f=inp.files&&inp.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{try{const keep=pvHist().slice(),o=JSON.parse(rd.result);if(!Array.isArray(o.pvHist)||o.pvHist.length<keep.length)o.pvHist=keep;mergeEst(o);""")
rep("""onclick="if(confirm('原価マスターを初期値に戻します。よろしいですか？')){EST=HC.defaults();saveEst();renderEst(true);}">""",
"""onclick="if(confirm('原価マスターを初期値に戻します（発行済みの価格版の履歴は残ります）。よろしいですか？')){const k=pvHist();EST=HC.defaults();EST.pvHist=k;saveEst();renderEst(true);}">""")

# ── 6) 起動：店舗版は社内機能を外す ──
rep("""function init(){
  loadEst();""","""function init(){
  if(!INTERNAL){document.querySelectorAll('.cbtn.est').forEach(e=>e.remove());const qi=$('qInt');if(qi)qi.closest('label').style.display='none';
    const ve=$('viewEst');if(ve)ve.innerHTML='';window.openEst=function(){};
    $('verLbl').textContent=`Heart Halo Ver. ${APP_VER} · 店舗用 · 価格版 ${PV_STORE.pv}（${PV_STORE.issued.slice(0,10)} 本社発行）`;}
  else $('verLbl').textContent=`Heart Halo Ver. ${APP_VER}（${APP_DATE}） · 社内用（原価・見積ボード） · 店舗版 ${pvNo()}`;
  if(INTERNAL)loadEst();""")
rep("""  if(location.hash==='#est')openEst();""","""  if(location.hash==='#est'&&INTERNAL)openEst();""")
open(dst,'w',encoding='utf-8').write(s);print('ok')
