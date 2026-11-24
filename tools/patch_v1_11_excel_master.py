import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding='utf-8').read()
def rep(old,new,cnt=1):
    global s
    n=s.count(old); assert n==cnt,(n,old[:100]); s=s.replace(old,new)

rep("const APP_VER='1.10.0'","const APP_VER='1.11.0'")
# ── 見積ボード上部のボタン ──
rep("""      <button class="cbtn pri" onclick="issueStore()">&#127980; 店舗版を発行</button>
      <input type="file" id="estFile" accept=".json,application/json" style="display:none" onchange="importEst(this)">""",
"""      <button class="cbtn" onclick="exportXlsx()">&#128202; Excel記入表</button>
      <button class="cbtn" onclick="document.getElementById('xlFile').click()">&#128229; 記入表を読込</button>
      <button class="cbtn pri" onclick="issueStore()">&#127980; 店舗版を発行</button>
      <input type="file" id="estFile" accept=".json,application/json" style="display:none" onchange="importEst(this)">
      <input type="file" id="xlFile" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" style="display:none" onchange="importXlsx(this)">""")
rep("""     <button class="cbtn" onclick="exportEst()">マスター保存（JSON）</button><button class="cbtn" onclick="$('estFile').click()">マスター読込</button>""",
"""     <button class="cbtn pri" onclick="exportXlsx()">Excel記入表を書き出し</button><button class="cbtn pri" onclick="$('xlFile').click()">記入表を読込（修正確認）</button></div><div class="row" style="margin-top:6px">
     <button class="cbtn" onclick="exportEst()">マスター保存（JSON）</button><button class="cbtn" onclick="$('estFile').click()">マスター読込</button>""")
# ── 発行：メモを外から渡せるように／本社版も同時に書き出し ──
rep("""function issueStore(){
  const T=HC.priceTable(EST),c=pvCur();
  if(c&&!pvDirty()){if(confirm('原価マスターは店舗版 '+c.no+'（'+c.date.slice(0,10)+' 発行）から変わっていません。\\n同じ '+c.no+' の店舗用アプリを書き出しますか？'))downloadStore(c);return;}
  const no='P'+String((c?pvSeq(c.no):0)+1).padStart(3,'0');
  const note=prompt(""","""function issueStore(noteIn){
  const T=HC.priceTable(EST),c=pvCur();
  if(c&&!pvDirty()){if(confirm('原価マスターは価格版 '+c.no+'（'+c.date.slice(0,10)+' 発行）から変わっていません。\\n同じ '+c.no+' の本社版・店舗版を書き出しますか？')){downloadStore(c);setTimeout(()=>downloadHQ(c),600);}return;}
  const no=pvNextNo();
  const note=noteIn!=null?noteIn:prompt(""")
rep("""  pvHist().push(h);saveEst();renderEst(true);downloadStore(h);
}""","""  pvHist().push(h);saveEst();renderEst(true);downloadStore(h);setTimeout(()=>downloadHQ(h),600);
  return h;
}
function pvNextNo(){const c=pvCur();return 'P'+String((c?pvSeq(c.no):0)+1).padStart(3,'0');}""")
rep("""<td class="c" style="white-space:nowrap"><button class="cbtn" onclick="pvRedownload('${h.no}')">店舗版を再出力</button>""",
"""<td class="c" style="white-space:nowrap"><button class="cbtn" onclick="pvRedownload('${h.no}')">店舗版を再出力</button> <button class="cbtn" onclick="downloadHQ(pvFind('${h.no}'))">本社版を出力</button>""")
# 店舗版の組立：本社版に埋め込んだマスター（pvSeed）は絶対に入れない
rep("""  all.slice(i0+1,n).forEach(x=>{if(x.src)return;let t=""","""  all.slice(i0+1,n).forEach(x=>{if(x.src||x.id==='pvSeed')return;let t=""")
rep("""const bad=['HQ_ONLY_'+'BEGIN',""","""const bad=['HQ_ONLY_'+'BEGIN','PV_HQ_'+'SEED',""")

# ── 新機能本体（社内専用領域の末尾に追加）──
NEW=r"""
/* ═════════ 本社版の書き出し（その価格版の原価マスター入り）═════════
   本社版ファイル自体に原価マスターと発行履歴を埋め込む。別PC・ブラウザでもこのファイルを開けば同じマスターで動く。 */
function buildHQHTML(h){
  const all=[...document.scripts],i0=all.findIndex(x=>x.id==='pvTop'),n=window.__PV_NS||all.length;
  if(i0<0||!window.__PV_TOP)throw new Error('元データを取得できません');
  const top=window.__PV_TOP.replace(/<\/body>\s*<\/html>\s*$/i,'');
  const seed={est:JSON.parse(JSON.stringify(EST)),pv:h?h.no:pvNo(),saved:new Date().toISOString(),appVer:APP_VER};
  const out=['<!DOCTYPE html>\n',top,'\n<script id="pvSeed">/* 本社版：価格版 '+seed.pv+' の原価マスター（社外秘） */\nwindow.PV_HQ_'+'SEED='+JSON.stringify(seed).replace(/</g,'\\u003c')+';\n</'+'script>'];
  all.slice(i0+1,n).forEach(x=>{if(x.src||x.id==='pvSeed')return;out.push('\n',x.outerHTML);});
  out.push('\n</body>\n</html>\n');return out.join('');
}
function downloadHQ(h){
  try{const html=buildHQHTML(h),no=h?h.no:pvNo();const a=document.createElement('a');a.download=`PonteVecchio_HeartHalo_本社版_V${APP_VER}_${no}.html`;
    a.href=URL.createObjectURL(new Blob([html],{type:'text/html'}));a.click();}
  catch(e){alert('本社版を書き出せませんでした：'+e.message);}
}
/* 本社版ファイルに入っているマスターを、このPCのマスターより新しければ取り込む */
function hqSeedCheck(){
  const sd=window.PV_HQ_SEED;if(!sd||!sd.est)return;
  const sh=sd.est.pvHist||[],sSeq=sh.length?pvSeq(sh[sh.length-1].no):0,lSeq=pvCur()?pvSeq(pvCur().no):0;
  let hasLocal=false;try{hasLocal=!!localStorage.getItem(EST_KEY);}catch(e){}
  if(hasLocal&&sSeq<=lSeq)return;
  if(hasLocal&&!confirm('このファイルには価格版 '+sd.pv+' の原価マスターが入っています（このPCは '+(pvCur()?pvCur().no:'未発行')+'）。\n新しい '+sd.pv+' のマスターに切り替えますか？'))return;
  mergeEst(sd.est);EST.updated=new Date().toISOString();try{localStorage.setItem(EST_KEY,JSON.stringify(EST));}catch(e){}
}

/* ═════════ Excel 記入表（原価マスターの確認・修正）═════════ */
const ROUND_LBL={down:'切捨て',up:'切上げ'},SZP_LBL={band:'サイズ帯（#13以下／#14以上）',each:'号ごと',one:'全サイズ共通（#20基準）'};
function masterItems(){
  const L=[],add=(k,grp,item,tgt,unit,type)=>L.push({k,grp,item,tgt,unit,type:type||'n'});
  add('margin','価格計算','粗利率','全アイテム','%');add('supMargin','価格計算','仕入先マージン','全アイテム','%');add('tax','価格計算','消費税率','全アイテム','%');
  add('round','価格計算','端数処理','全アイテム','切捨て／切上げ','t');add('sizePrice','価格計算','リングの価格サイズ','リング','サイズ帯／号ごと／全サイズ共通','t');
  HH.METALS.forEach(m=>{add('metals|'+m+'|price','1 地金','地金単価',m,'円/g');add('metals|'+m+'|dens','1 地金','比重係数（K18＝1.00）',m,'倍');add('metals|'+m+'|labor','1 地金','工賃係数',m,'倍');});
  HH.MELEE.forEach(x=>add('dia|'+x.mm.toFixed(1),'2 メレーダイヤ','ダイヤ単価 Ø'+x.mm.toFixed(1)+'（'+x.lbl+'）','径 '+x.mm.toFixed(1)+'mm','円/ct'));
  const sk=['NL','RA','RB'];
  sk.forEach(s=>HH.C_SIZES.forEach(c=>add('sku|'+s+'|head|'+c,'3 重量','頭部重量（K18換算）',SKU_SHORT[s]+' 中石'+c.toFixed(1)+'mm','g')));
  ['RA','RB'].forEach(s=>{add('sku|'+s+'|shank13','3 重量','腕重量 #13基準（K18換算）',SKU_SHORT[s],'g');add('sku|'+s+'|perGo','3 重量','1号あたりの増減',SKU_SHORT[s],'g/号');});
  [['cast','キャスト'],['assy','組み'],['polish','磨き'],['other','その他'],['setSide','留め（脇石）1石'],['setCenter','留め（中石）1石']].forEach(([k,l])=>sk.forEach(s=>add('sku|'+s+'|'+k,'4 工賃・留め',l,SKU_SHORT[s],'円')));
  HH.METALS.forEach(m=>add('sku|NL|chain|'+m,'5 チェーン・金具','チェーン・金具',SKU_SHORT.NL+' '+m,'円'));
  return L;
}
function itemDisp(it,v){if(it.k==='round')return ROUND_LBL[v]||v;if(it.k==='sizePrice')return SZP_LBL[v]||v;return v;}
function itemParse(it,raw){
  if(raw==null)return null;let t=String(raw).trim();if(t==='')return null;
  if(it.k==='round'){if(/上|up/i.test(t))return 'up';if(/捨|down/i.test(t))return 'down';throw new Error(it.item+'：「切捨て」か「切上げ」で記入してください（'+t+'）');}
  if(it.k==='sizePrice'){if(/帯|band/i.test(t))return 'band';if(/号|each/i.test(t))return 'each';if(/共通|one/i.test(t))return 'one';throw new Error(it.item+'：「サイズ帯」「号ごと」「全サイズ共通」のいずれかで記入してください（'+t+'）');}
  t=t.replace(/[０-９．]/g,ch=>String.fromCharCode(ch.charCodeAt(0)-0xFEE0));const n=numv(t);
  if(n==null||!isFinite(n))throw new Error(it.item+'（'+it.tgt+'）：数値として読めません「'+t+'」');
  if(n<0)throw new Error(it.item+'（'+it.tgt+'）：マイナスは記入できません');return n;
}
/* ── xlsx 書き出し（外部ライブラリなし・無圧縮ZIP）── */
const CRC_T=(()=>{const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(u){let c=-1;for(let i=0;i<u.length;i++)c=CRC_T[(c^u[i])&255]^(c>>>8);return (c^-1)>>>0;}
function zipStore(files){
  const enc=new TextEncoder(),parts=[],cen=[];let off=0;
  files.forEach(f=>{const nm=enc.encode(f.name),d=typeof f.data==='string'?enc.encode(f.data):f.data,cr=crc32(d);
    const lh=new DataView(new ArrayBuffer(30));lh.setUint32(0,0x04034b50,true);lh.setUint16(4,20,true);lh.setUint16(6,0x0800,true);lh.setUint32(14,cr,true);lh.setUint32(18,d.length,true);lh.setUint32(22,d.length,true);lh.setUint16(26,nm.length,true);
    parts.push(lh,nm,d);
    const ch=new DataView(new ArrayBuffer(46));ch.setUint32(0,0x02014b50,true);ch.setUint16(4,20,true);ch.setUint16(6,20,true);ch.setUint16(8,0x0800,true);ch.setUint32(16,cr,true);ch.setUint32(20,d.length,true);ch.setUint32(24,d.length,true);ch.setUint16(28,nm.length,true);ch.setUint32(42,off,true);
    cen.push(ch,nm);off+=30+nm.length+d.length;});
  const cs=cen.reduce((a,x)=>a+(x.byteLength||x.length),0),e=new DataView(new ArrayBuffer(22));
  e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,cs,true);e.setUint32(16,off,true);
  return new Blob([...parts,...cen,e],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
}
function xesc(v){return String(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function colL(i){let s='';i++;while(i){const m=(i-1)%26;s=String.fromCharCode(65+m)+s;i=(i-1-m)/26|0;}return s;}
function sheetXml(rows,opt){
  opt=opt||{};let x='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">';
  if(opt.freeze)x+=`<sheetViews><sheetView workbookViewId="0"><pane ySplit="${opt.freeze}" topLeftCell="A${opt.freeze+1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>`;
  if(opt.cols)x+='<cols>'+opt.cols.map((w,i)=>`<col min="${i+1}" max="${i+1}" width="${w}" customWidth="1"${opt.hide&&opt.hide.includes(i)?' hidden="1"':''}/>`).join('')+'</cols>';
  x+='<sheetData>';
  rows.forEach((r,ri)=>{if(!r)return;x+=`<row r="${ri+1}"${r.ht?` ht="${r.ht}" customHeight="1"`:''}>`;(r.c||r).forEach((c,ci)=>{if(c==null)return;const o=typeof c==='object'?c:{v:c},ref=colL(ci)+(ri+1),st=o.s?` s="${o.s}"`:'';
      if(o.v==null||o.v==='')x+=`<c r="${ref}"${st}/>`;else if(typeof o.v==='number')x+=`<c r="${ref}"${st}><v>${o.v}</v></c>`;else x+=`<c r="${ref}"${st} t="inlineStr"><is><t xml:space="preserve">${xesc(o.v)}</t></is></c>`;});x+='</row>';});
  x+='</sheetData>';if(opt.merge)x+='<mergeCells count="'+opt.merge.length+'">'+opt.merge.map(m=>`<mergeCell ref="${m}"/>`).join('')+'</mergeCells>';
  return x+'<pageMargins left="0.4" right="0.4" top="0.5" bottom="0.5" header="0.3" footer="0.3"/><pageSetup paperSize="9" orientation="portrait" fitToHeight="0"/></worksheet>';
}
const XL_STYLES=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="2"><numFmt numFmtId="164" formatCode="#,##0.####"/><numFmt numFmtId="165" formatCode="&quot;¥&quot;#,##0"/></numFmts>
<fonts count="4"><font><sz val="11"/><name val="Yu Gothic"/><family val="3"/><charset val="128"/></font><font><b/><sz val="11"/><name val="Yu Gothic"/><family val="3"/><charset val="128"/></font><font><b/><sz val="15"/><color rgb="FF1E2A50"/><name val="Yu Gothic"/><family val="3"/><charset val="128"/></font><font><sz val="9"/><color rgb="FF888888"/><name val="Yu Gothic"/><family val="3"/><charset val="128"/></font></fonts>
<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE8DCC2"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF2A8"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFBBBBBB"/></left><right style="thin"><color rgb="FFBBBBBB"/></right><top style="thin"><color rgb="FFBBBBBB"/></top><bottom style="thin"><color rgb="FFBBBBBB"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="9"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
<xf numFmtId="164" fontId="1" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyProtection="1"><protection locked="0"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="164" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>
<xf numFmtId="0" fontId="3" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
<xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyProtection="1"><protection locked="0"/></xf>
<xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1"/></cellXfs>
<cellStyles count="1"><cellStyle name="標準" xfId="0" builtinId="0"/></cellStyles></styleSheet>`;
function exportXlsx(){
  const items=masterItems(),pv=pvNo(),d=new Date(),ds=d.toISOString().slice(0,10);
  const R=[];
  R[0]={c:[{v:'Heart Halo　原価マスター 記入表（社外秘）',s:3}],ht:24};
  R[1]=[{v:'現行価格版'},{v:pv},null,{v:'出力日'},{v:ds},{v:'本社版'},{v:'V'+APP_VER}];
  R[2]=[{v:'記入方法：黄色の「新しい値」欄に、変更する項目だけ記入してください。空欄＝変更なし。A列（キー）と行の並びは変更しないでください。'}];
  R[3]=[{v:'記入後、本社版アプリ「見積ボード」→「記入表を読込」で修正箇所を確認し、新しい価格版として登録します。'}];
  R[4]={c:['キー','区分','項目','対象','単位','現在値（'+pv+'）','新しい値（記入）','変更理由・メモ'].map(v=>({v,s:1})),ht:30};
  items.forEach((it,i)=>{const cur=getP(it.k);R[5+i]=[{v:it.k,s:6},{v:it.grp,s:5},{v:it.item,s:5},{v:it.tgt,s:5},{v:it.unit,s:5},{v:it.type==='t'?itemDisp(it,cur):(numv(cur)??''),s:4},{v:'',s:it.type==='t'?7:2},{v:'',s:7}];});
  const s1=sheetXml(R,{freeze:5,cols:[22,14,30,20,12,16,18,36],merge:['A1:H1','A3:H3','A4:H4']});
  /* 参考：現行の販売価格（税込） */
  const P=[{c:[{v:'参考：現在のマスターでの販売価格（枠・税込・中石別）　'+pv,s:3}],ht:24},[{v:'※ 記入表の新しい値を反映した後の価格は、アプリの確認画面に表示されます。'}]];
  const ring=s=>HH.SKUS.find(x=>x.id===s).ring,zs=EST.sizePrice==='band'?[13,20]:EST.sizePrice==='one'?[20]:HH.R_SIZES;
  P.push({c:['アイテム','地金','サイズ'].concat(HH.C_SIZES.map(c=>'中石 '+c.toFixed(1)+'mm')).map(v=>({v,s:1})),ht:22});
  ['NL','RA','RB'].forEach(s=>HH.METALS.forEach(m=>(ring(s)?zs:[null]).forEach(z=>{
    P.push([{v:SKU_SHORT[s],s:5},{v:m,s:5},{v:z==null?'45cm':(EST.sizePrice==='band'?(z===13?'#13以下':'#14以上'):'#'+z),s:5}].concat(HH.C_SIZES.map(c=>{const r=HC.costOf(EST,s,m,c,z);return {v:r.P?r.P.inc:'',s:8};})));})));
  const s2=sheetXml(P,{freeze:3,cols:[12,9,10].concat(HH.C_SIZES.map(()=>13))});
  const ct=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>`;
  const rels=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`;
  const wb=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="記入表" sheetId="1" r:id="rId1"/><sheet name="販売価格（参考）" sheetId="2" r:id="rId2"/></sheets><definedNames><definedName name="_xlnm.Print_Titles" localSheetId="0">記入表!$5:$5</definedName></definedNames></workbook>`;
  const wrels=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`;
  const blob=zipStore([{name:'[Content_Types].xml',data:ct},{name:'_rels/.rels',data:rels},{name:'xl/workbook.xml',data:wb},{name:'xl/_rels/workbook.xml.rels',data:wrels},{name:'xl/styles.xml',data:XL_STYLES},{name:'xl/worksheets/sheet1.xml',data:s1},{name:'xl/worksheets/sheet2.xml',data:s2}]);
  const a=document.createElement('a');a.download=`PV_HeartHalo_原価マスター記入表_${pv.replace(/[^\w]/g,'')}_${ds.replace(/-/g,'')}.xlsx`;a.href=URL.createObjectURL(blob);a.click();
}
/* ── xlsx 読込（Excelで保存した圧縮ZIPにも対応：ブラウザ標準の DecompressionStream を使用）── */
async function unzipXlsx(buf){
  const u8=new Uint8Array(buf),dv=new DataView(buf);let e=u8.length-22;while(e>=0&&dv.getUint32(e,true)!==0x06054b50)e--;
  if(e<0)throw new Error('Excel（.xlsx）ファイルではありません');
  const n=dv.getUint16(e+10,true);let p=dv.getUint32(e+16,true);const F={},td=new TextDecoder();
  for(let i=0;i<n;i++){const m=dv.getUint16(p+10,true),cs=dv.getUint32(p+20,true),nl=dv.getUint16(p+28,true),xl=dv.getUint16(p+30,true),cl=dv.getUint16(p+32,true),lo=dv.getUint32(p+42,true);
    const name=td.decode(u8.subarray(p+46,p+46+nl)),ds=lo+30+dv.getUint16(lo+26,true)+dv.getUint16(lo+28,true);F[name]={m,raw:u8.subarray(ds,ds+cs)};p+=46+nl+xl+cl;}
  return async name=>{const f=F[name];if(!f)return null;let d=f.raw;
    if(f.m===8){if(typeof DecompressionStream==='undefined')throw new Error('このブラウザはExcelファイルの読込に対応していません（Chrome・Edge・Safari の最新版をお使いください）');
      d=new Uint8Array(await new Response(new Blob([d]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer());}
    else if(f.m!==0)throw new Error('対応していない圧縮形式です');return td.decode(d);};
}
async function readSheet(buf,sheetName){
  const get=await unzipXlsx(buf),P=t=>new DOMParser().parseFromString(t,'application/xml'),T=(n,tag)=>[...n.getElementsByTagNameNS('*',tag)];
  const wb=P(await get('xl/workbook.xml')),rl=P(await get('xl/_rels/workbook.xml.rels'));
  const sh=T(wb,'sheet').find(x=>x.getAttribute('name')===sheetName)||T(wb,'sheet')[0];if(!sh)throw new Error('シートが見つかりません');
  const rid=sh.getAttribute('r:id')||sh.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships','id');
  let tgt=T(rl,'Relationship').find(x=>x.getAttribute('Id')===rid).getAttribute('Target');tgt=tgt.replace(/^\/?xl\//,'').replace(/^\//,'');
  const ssT=await get('xl/sharedStrings.xml'),ss=ssT?T(P(ssT),'si').map(si=>T(si,'t').map(t=>t.textContent).join('')):[];
  const ws=P(await get('xl/'+tgt)),rows={};
  T(ws,'c').forEach(c=>{const ref=c.getAttribute('r'),m=/^([A-Z]+)(\d+)$/.exec(ref);if(!m)return;const t=c.getAttribute('t'),v=T(c,'v')[0];let val=null;
    if(t==='s')val=v?ss[+v.textContent]:null;else if(t==='inlineStr')val=T(c,'t').map(x=>x.textContent).join('');else if(t==='b')val=v?v.textContent==='1':null;else val=v?(t==='str'||t==='e'?v.textContent:+v.textContent):null;
    (rows[+m[2]]=rows[+m[2]]||{})[m[1]]=val;});
  return rows;
}
let XL_PENDING=null;
async function importXlsx(inp){
  const f=inp.files&&inp.files[0];inp.value='';if(!f)return;
  try{const rows=await readSheet(await f.arrayBuffer(),'記入表'),items=masterItems(),byK=Object.fromEntries(items.map(x=>[x.k,x]));
    const pvSheet=String((rows[2]||{}).B||''),changes=[],errs=[],seen=new Set();
    Object.keys(rows).map(Number).sort((a,b)=>a-b).forEach(r=>{if(r<6)return;const R=rows[r],k=R.A;if(!k)return;const it=byK[String(k).trim()];
      if(!it){errs.push(r+'行目：キー「'+k+'」はこのアプリにありません');return;}seen.add(it.k);
      let nv;try{nv=itemParse(it,R.G);}catch(e){errs.push(r+'行目：'+e.message);return;}if(nv==null)return;
      const cur=getP(it.k),cv=it.type==='t'?cur:numv(cur);if(it.type==='t'?nv===cv:(cv!=null&&Math.abs(nv-cv)<1e-9))return;
      changes.push({it,row:r,cur:cv,nv,memo:String(R.H||'').trim()});});
    if(!seen.size)throw new Error('記入表の形式が違います（「記入表」シートのA列にキーがありません）');
    if(errs.length){alert('記入表に読めない箇所があります。修正して読み込み直してください。\n\n'+errs.slice(0,15).join('\n')+(errs.length>15?'\n…ほか'+(errs.length-15)+'件':''));return;}
    if(!changes.length){alert('記入表に変更はありませんでした（「新しい値」が空欄、または現在値と同じ）。');return;}
    XL_PENDING={changes,pvSheet,file:f.name};showXlDiff();
  }catch(e){alert('記入表を読み込めませんでした：'+e.message);}
}
function applyChanges(M,changes){changes.forEach(c=>{const ks=c.it.k.split('|');let o=M;for(let i=0;i<ks.length-1;i++)o=o[ks[i]];o[ks[ks.length-1]]=c.nv;});return M;}
function showXlDiff(){
  const P=XL_PENDING,ch=P.changes,after=applyChanges(JSON.parse(JSON.stringify(EST)),ch);
  const Tb=HC.priceTable(EST),Ta=HC.priceTable(after);let nAll=0,nChg=0,maxUp=0,maxDn=0;
  Object.keys(Tb.prices).forEach(s=>Object.keys(Tb.prices[s]).forEach(m=>Object.keys(Tb.prices[s][m]).forEach(c=>{const b=Tb.prices[s][m][c],a=Ta.prices[s][m][c];
    (typeof b==='object'&&b?Object.keys(b).map(z=>[b[z],a[z]]):[[b,a]]).forEach(([x,y])=>{nAll++;if(x!==y){nChg++;if(x&&y){const r=y/x-1;maxUp=Math.max(maxUp,r);maxDn=Math.min(maxDn,r);}}});})));
  const fv=(it,v)=>it.type==='t'?esc(itemDisp(it,v)):(v==null?'—':(+v).toLocaleString('ja-JP',{maximumFractionDigits:4}));
  const rows=ch.map(c=>{const d=c.it.type==='t'||c.cur==null?'':c.nv-c.cur,pc=d===''||!c.cur?'':(d/c.cur*100);
    return `<tr><td>${esc(c.it.grp)}</td><td>${esc(c.it.item)}</td><td>${esc(c.it.tgt)}</td><td class="n">${fv(c.it,c.cur)}</td><td class="n"><b>${fv(c.it,c.nv)}</b></td><td class="n" style="color:${d>0?'#B0302A':d<0?'#2F6B3C':'inherit'}">${d===''?'':(d>0?'+':'')+(+d).toLocaleString('ja-JP',{maximumFractionDigits:4})}</td><td class="n">${pc===''?'':(pc>0?'+':'')+pc.toFixed(1)+'%'}</td><td>${esc(c.memo)}</td></tr>`;}).join('');
  const smp=[];['NL','RA','RB'].forEach(s=>HH.METALS.forEach(m=>{const z=s==='NL'?null:13,c=6,b=HC.costOf(EST,s,m,c,z),a=HC.costOf(after,s,m,c,z);
    smp.push(`<tr><td>${SKU_SHORT[s]}</td><td>${m}</td><td class="n">${fmt(b.cost)}</td><td class="n"><b>${fmt(a.cost)}</b></td><td class="n">${b.P?yen(b.P.inc):'—'}</td><td class="n"><b>${a.P?yen(a.P.inc):'—'}</b></td><td class="n" style="color:${a.P&&b.P&&a.P.inc!==b.P.inc?(a.P.inc>b.P.inc?'#B0302A':'#2F6B3C'):'inherit'}">${a.P&&b.P?(a.P.inc===b.P.inc?'±0':(a.P.inc>b.P.inc?'+':'')+(a.P.inc-b.P.inc).toLocaleString('ja-JP')):''}</td></tr>`);}));
  const no=pvNextNo(),cur=pvCur(),stale=P.pvSheet&&P.pvSheet!==pvNo();
  const autoNote=ch.map(c=>c.it.item.replace(/（.*?）/g,'')+' '+c.it.tgt+' '+(c.it.type==='t'?itemDisp(c.it,c.cur)+'→'+itemDisp(c.it,c.nv):fv(c.it,c.cur)+'→'+fv(c.it,c.nv))).join('、');
  let el=$('xlDiff');if(!el){el=document.createElement('div');el.id='xlDiff';document.body.appendChild(el);}
  el.innerHTML=`<div class="xd-box"><div class="xd-h"><b>記入表の修正内容の確認</b><span>${esc(P.file)}</span><button class="cbtn" onclick="closeXlDiff()">閉じる</button></div><div class="xd-b">
   ${stale?`<div class="callout ng" style="margin:0 0 10px">⚠ この記入表は価格版 <b>${esc(P.pvSheet)}</b> の時点で書き出されたものです（現在は ${pvNo()}）。「現在値」が今のマスターと違う項目は、下表の「現在」が今のマスターの値です。</div>`:''}
   <h4>修正箇所　${ch.length}項目</h4><table class="et2"><tr><th>区分</th><th>項目</th><th>対象</th><th>現在</th><th>新しい値</th><th>差</th><th>率</th><th>理由・メモ</th></tr>${rows}</table>
   <h4>売価への影響</h4><div class="callout ${nChg?'ng':'ok'}" style="margin:0 0 8px">販売価格表 ${nAll}件のうち <b>${nChg}件</b> が変わります${nChg?`（変動幅 ${(maxDn*100).toFixed(1)}% 〜 +${(maxUp*100).toFixed(1)}%）`:''}。</div>
   <table class="et2"><tr><th>アイテム</th><th>地金</th><th>原価 現在</th><th>原価 新</th><th>上代 現在</th><th>上代 新</th><th>差</th></tr>${smp.join('')}</table><p class="d">例：中石6.0mm・#13（ネックレスは45cm）。上代＝枠・税込。</p>
   <h4>登録</h4><label class="d" style="display:block;margin-bottom:4px">価格版 ${no} の発行メモ</label><textarea id="xdNote" rows="3" style="width:100%;font:inherit;font-size:12px">${esc(autoNote)}</textarea>
   <div class="xd-f"><button class="cbtn pri" onclick="applyXl(true)">反映して 新しい価格版 ${no} を登録（本社版・店舗版を書き出し）</button><button class="cbtn" onclick="applyXl(false)">マスターに反映のみ（発行しない）</button><button class="cbtn" onclick="closeXlDiff()">キャンセル</button></div>
   <p class="d">登録すると、この時点の原価と販売価格が ${no} として確定し、${cur?cur.no+' の店舗版は旧版になります。':''}本社版（${no} のマスター入り）と店舗版（原価なし）の2ファイルがダウンロードされます。店舗へは店舗版を送ってください。</p></div></div>`;
  el.classList.add('on');
}
function closeXlDiff(){const el=$('xlDiff');if(el)el.classList.remove('on');}
function applyXl(issue){
  const P=XL_PENDING;if(!P)return;const note=($('xdNote')||{}).value||'';
  applyChanges(EST,P.changes);saveEst();XL_PENDING=null;closeXlDiff();renderEst(true);
  if(issue){const h=issueStore(note);if(h)alert('価格版 '+h.no+' を登録しました。\n本社版・店舗版の2ファイルを書き出しました。店舗へは「店舗用_'+h.no+'」を送ってください。');}
  else alert('マスターに反映しました（未発行）。店舗の価格は '+(pvCur()?pvCur().no:'未発行')+' のままです。');
}
"""
rep("/*@@HQ_ONLY_END@@*/","/*@@HQ_ONLY_BEGIN_X@@*/".replace('_X','')[:0]+NEW+"/*@@HQ_ONLY_END@@*/")
# 起動時：本社版ファイルのマスター取込
rep("  if(INTERNAL)loadEst();","  if(INTERNAL){loadEst();hqSeedCheck();}")
# 確認画面のスタイル
rep(".callout{margin-top:10px;",""".callout{margin-top:10px;""")
rep("</style>","""#xlDiff{position:fixed;inset:0;z-index:80;background:rgba(30,25,15,.45);display:none;align-items:flex-start;justify-content:center;padding:28px 12px;overflow:auto;}
#xlDiff.on{display:flex;}
#xlDiff .xd-box{background:#FDFAF5;border-radius:14px;max-width:980px;width:100%;box-shadow:0 10px 40px rgba(0,0,0,.25);}
#xlDiff .xd-h{display:flex;gap:12px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--border);}
#xlDiff .xd-h span{flex:1;color:var(--txt3);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
#xlDiff .xd-b{padding:12px 16px 16px;font-size:12px;}
#xlDiff h4{margin:14px 0 6px;color:var(--gold-d);letter-spacing:1px;}
#xlDiff table.et2{width:100%;}
#xlDiff .xd-f{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 6px;}
</style>""",1) if s.count("</style>")==1 else None
open(dst,'w',encoding='utf-8').write(s);print('ok', s.count('</style>'))
