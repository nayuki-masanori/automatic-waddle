/**
 * Sumisura 受注アプリ（Google Apps Script版）サーバー側
 *
 * ・Chromeで開くWebアプリ。AIはGemini（API）だけを使う。
 * ・データは会社のGoogleスプレッドシート、画像とPDFは会社のGoogleドライブに保存する。
 * ・「本社メンバー」シートにあるアカウントだけが、案件（原価・見積）と原価マスターを読み書きできる。
 *   店舗のアカウントには、カルテと見積書（お客様向け）しか届かない。
 *
 * 最初に一度だけ：エディタで関数「setup」を実行する（設置手順書 参照）。
 */

const PROPS_ = PropertiesService.getScriptProperties();
const COLS_ = ['kartes', 'cases', 'proposals', 'master'];
const CHUNK_ = 40000;           // 1セルに入れる文字数（上限 50,000 の手前）
const READ_ = {kartes: ['hq', 'store'], proposals: ['hq', 'store'], cases: ['hq'], master: ['hq']};
const WRITE_ = {kartes: ['hq', 'store'], proposals: ['hq'], cases: ['hq'], master: ['hq']};

/* ───────── 画面 ───────── */
function doGet(e) {
  // Index.html が Styles・AppA・AppB を読み込んで1枚の画面にする（4ファイル構成）
  return HtmlService.createTemplateFromFile('Index').evaluate()
    .setTitle('Sumisura 受注アプリ')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/** 分けたHTMLファイルの中身をそのまま差し込む（Index.html から呼ぶ） */
function include(name) {
  return HtmlService.createHtmlOutputFromFile(name).getContent();
}

/* ───────── 初期設定（管理者が一度だけ実行）───────── */
function setup() {
  let ssId = PROPS_.getProperty('SHEET_ID'), folderId = PROPS_.getProperty('FOLDER_ID');
  let ss = ssId ? SpreadsheetApp.openById(ssId) : null;
  if (!ss) { ss = SpreadsheetApp.create('Sumisura_受注データ'); PROPS_.setProperty('SHEET_ID', ss.getId()); }
  COLS_.forEach(c => { if (!ss.getSheetByName(c)) { const sh = ss.insertSheet(c); sh.appendRow(['id', '更新日時', '更新者', '概要', 'data']); sh.setFrozenRows(1); } });
  let mem = ss.getSheetByName('本社メンバー');
  if (!mem) {
    mem = ss.insertSheet('本社メンバー');
    mem.appendRow(['メールアドレス', 'お名前', 'メモ']);
    const me = Session.getEffectiveUser().getEmail();
    if (me) mem.appendRow([me, '', '設置した人（自動）']);
    mem.setFrozenRows(1);
  }
  let log = ss.getSheetByName('ログ');
  if (!log) { log = ss.insertSheet('ログ'); log.appendRow(['日時', 'アカウント', '操作', '対象']); log.setFrozenRows(1); }
  const s1 = ss.getSheetByName('シート1') || ss.getSheetByName('Sheet1');
  if (s1 && ss.getSheets().length > 1) ss.deleteSheet(s1);
  if (!folderId) { const f = DriveApp.createFolder('Sumisura_画像・PDF'); PROPS_.setProperty('FOLDER_ID', f.getId()); }
  // 原価マスターの初期値（本社だけが読める）
  if (!readDoc_('master', 'defaults')) writeDoc_('master', 'defaults', MASTER_DEFAULTS, 'setup');
  if (!PROPS_.getProperty('GEMINI_MODEL')) PROPS_.setProperty('GEMINI_MODEL', 'gemini-3.8-flash');
  if (!PROPS_.getProperty('GEMINI_IMAGE_MODEL')) PROPS_.setProperty('GEMINI_IMAGE_MODEL', 'gemini-nano-banana-2.1');
  Logger.log('データ用スプレッドシート: ' + ss.getUrl());
  Logger.log('画像・PDFフォルダ: https://drive.google.com/drive/folders/' + PROPS_.getProperty('FOLDER_ID'));
  return {sheet: ss.getUrl(), folder: PROPS_.getProperty('FOLDER_ID')};
}

/* ───────── 権限 ───────── */
function email_() { return String(Session.getActiveUser().getEmail() || '').toLowerCase(); }
function ss_() {
  const id = PROPS_.getProperty('SHEET_ID');
  if (!id) throw new Error('[unavailable] 初期設定がまだです（setup を実行してください）');
  return SpreadsheetApp.openById(id);
}
function isHq_(email) {
  if (!email) return false;
  const sh = ss_().getSheetByName('本社メンバー');
  if (!sh || sh.getLastRow() < 2) return false;
  return sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().some(r => String(r[0]).trim().toLowerCase() === email);
}
function role_() { return isHq_(email_()) ? 'hq' : 'store'; }
function need_(table, col, role) {
  if (COLS_.indexOf(col) < 0) throw new Error('[invalid] 不明なデータです：' + col);
  if (table[col].indexOf(role) < 0) throw new Error('[permission_denied] この操作は本社だけができます');
}

/* ───────── 起動 ───────── */
function apiBoot(o) {
  const email = email_(), hq = isHq_(email);
  const view = String((o && o.view) || '');
  const key = !!PROPS_.getProperty('GEMINI_API_KEY');
  return {
    email: email, role: hq && view !== 'store' ? 'hq' : 'store', isHq: hq,
    gemini: key, geminiImage: key && !!PROPS_.getProperty('GEMINI_IMAGE_MODEL'),
    company: PROPS_.getProperty('COMPANY_NAME') || ''
  };
}

/* ───────── データ（スプレッドシート：1行＝1件、JSONを複数セルに分けて保存）───────── */
function sheet_(col) {
  const sh = ss_().getSheetByName(col);
  if (!sh) throw new Error('[unavailable] シート「' + col + '」がありません（setup を実行してください）');
  return sh;
}
function rows_(col) {
  const sh = sheet_(col), n = sh.getLastRow();
  if (n < 2) return [];
  return sh.getRange(2, 1, n - 1, sh.getLastColumn()).getValues();
}
function parseRow_(r) { const t = r.slice(4).join(''); return t ? JSON.parse(t) : null; }
function readDoc_(col, id) { const r = rows_(col).find(x => String(x[0]) === id); return r ? parseRow_(r) : null; }
function readAll_(col) { const o = {}; rows_(col).forEach(r => { if (r[0]) o[String(r[0])] = parseRow_(r); }); return o; }
function summary_(col, d) {
  if (!d) return '';
  if (col === 'kartes') return [d.name, d.store, d.staff, d.status].filter(x => x).join(' / ');
  if (col === 'cases') return [d.no, d.name || (d.k && d.k.name), d.status].filter(x => x).join(' / ');
  if (col === 'proposals') return [d.no, d.name].filter(x => x).join(' / ');
  return '';
}
function writeDoc_(col, id, doc, who) {
  const sh = sheet_(col), json = JSON.stringify(doc);
  const parts = []; for (let i = 0; i < json.length; i += CHUNK_) parts.push(json.slice(i, i + CHUNK_));
  if (!parts.length) parts.push('');
  const row = [id, new Date(), who || '', summary_(col, doc)].concat(parts);
  const ids = sh.getLastRow() < 2 ? [] : sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().map(r => String(r[0]));
  const at = ids.indexOf(id), width = Math.max(sh.getLastColumn(), row.length);
  while (row.length < width) row.push('');
  if (sh.getMaxColumns() < width) sh.insertColumnsAfter(sh.getMaxColumns(), width - sh.getMaxColumns());
  if (at >= 0) sh.getRange(at + 2, 1, 1, width).setValues([row]);
  else sh.getRange(sh.getLastRow() + 1, 1, 1, width).setValues([row]);
  bump_(col);
}
function bump_(col) { const v = +(PROPS_.getProperty('v_' + col) || 0) + 1; PROPS_.setProperty('v_' + col, String(v)); return v; }
function ver_(col) { return +(PROPS_.getProperty('v_' + col) || 0); }
function log_(op, target) { try { ss_().getSheetByName('ログ').appendRow([new Date(), email_(), op, target]); } catch (e) {} }
function checkId_(id) { if (!/^[\w.-]{1,80}$/.test(String(id || ''))) throw new Error('[invalid] IDが正しくありません'); return String(id); }

function apiPull(o) {
  const role = role_(), out = {cols: {}, denied: {}}, vers = (o && o.vers) || {};
  ((o && o.cols) || []).forEach(c => {
    if (COLS_.indexOf(c) < 0) return;
    if (READ_[c].indexOf(role) < 0) { out.denied[c] = '本社だけが見られるデータです'; return; }
    const v = ver_(c);
    if (vers[c] === v && v > 0) return;
    let docs = readAll_(c);
    if (c === 'master') { const m = {}; if (docs.main) m.main = docs.main; docs = m; }   // 初期値（defaults）は apiGet で
    out.cols[c] = {v: v, docs: docs};
  });
  return out;
}
function apiGet(o) { const role = role_(); need_(READ_, o.col, role); return readDoc_(o.col, checkId_(o.id)); }
function apiSet(o) {
  const role = role_(); need_(WRITE_, o.col, role); const id = checkId_(o.id);
  if (o.col === 'master' && id === 'defaults') throw new Error('[permission_denied] 初期値は書き換えられません');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try { writeDoc_(o.col, id, o.doc, email_()); return {v: ver_(o.col)}; }
  finally { lock.releaseLock(); }
}
function apiDelete(o) {
  const role = role_(); need_(WRITE_, o.col, role); const id = checkId_(o.id);
  if (o.col === 'kartes' && role !== 'hq') {
    const d = readDoc_('kartes', id);
    if (d && d.status && d.status !== '下書き') throw new Error('[permission_denied] 送信済みのカルテは店舗から削除できません');
  }
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const sh = sheet_(o.col);
    if (sh.getLastRow() >= 2) {
      const ids = sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().map(r => String(r[0]));
      const at = ids.indexOf(id); if (at >= 0) sh.deleteRow(at + 2);
    }
    bump_(o.col); log_('削除', o.col + '/' + id);
    return {v: ver_(o.col)};
  } finally { lock.releaseLock(); }
}

/* ───────── 画像・PDF（ドライブ）───────── */
function folder_() {
  const id = PROPS_.getProperty('FOLDER_ID');
  if (!id) throw new Error('[unavailable] 初期設定がまだです（setup を実行してください）');
  return DriveApp.getFolderById(id);
}
function ownFile_(id) {
  const f = DriveApp.getFileById(String(id)), fid = PROPS_.getProperty('FOLDER_ID'), it = f.getParents();
  while (it.hasNext()) if (it.next().getId() === fid) return f;
  throw new Error('[permission_denied] このアプリのファイルではありません');
}
function apiUpload(o) {
  const mime = String(o.mime || 'application/octet-stream');
  if (!/^(image\/(png|jpeg|webp|gif)|application\/pdf)$/.test(mime)) throw new Error('[invalid] 画像かPDFだけ保存できます');
  const bytes = Utilities.base64Decode(o.b64);
  if (bytes.length > 20 * 1024 * 1024) throw new Error('[too_large] 20MBまでです');
  const name = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd_HHmmss') + '_' + String(o.name || 'file').replace(/[\\/:*?"<>|]/g, '_').slice(0, 80);
  const f = folder_().createFile(Utilities.newBlob(bytes, mime, name));
  f.setDescription('Sumisura / ' + email_());
  return {id: f.getId(), size: bytes.length};
}
function apiAsset(id) { const f = ownFile_(id), b = f.getBlob(); return {mime: b.getContentType(), b64: Utilities.base64Encode(b.getBytes()), name: f.getName()}; }
function apiDeleteAsset(id) { if (role_() !== 'hq') throw new Error('[permission_denied] 本社だけが削除できます'); ownFile_(id).setTrashed(true); return true; }

/* ───────── Gemini ───────── */
function gemini_(model, body) {
  const key = PROPS_.getProperty('GEMINI_API_KEY');
  if (!key) throw new Error('[not_granted] Gemini APIキーが設定されていません（設置手順書 4）');
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent';
  const res = UrlFetchApp.fetch(url, {method: 'post', contentType: 'application/json', headers: {'x-goog-api-key': key}, payload: JSON.stringify(body), muteHttpExceptions: true});
  const code = res.getResponseCode(), txt = res.getContentText();
  if (code !== 200) {
    let m = txt; try { m = JSON.parse(txt).error.message; } catch (e) {}
    throw new Error('[' + (code === 429 ? 'rate_limited' : code === 403 ? 'not_granted' : 'gemini_error') + '] Gemini: ' + String(m).slice(0, 300));
  }
  return JSON.parse(txt);
}
function parts_(o) {
  const p = (o.images || []).slice(0, 6).map(im => ({inline_data: {mime_type: im.mime || 'image/png', data: im.b64}}));
  p.push({text: String(o.prompt || '')});
  return p;
}
function apiGeminiJson(o) {
  if (role_() !== 'hq') throw new Error('[permission_denied] 本社だけが使えます');
  const r = gemini_(PROPS_.getProperty('GEMINI_MODEL') || 'gemini-3.8-flash', {
    contents: [{role: 'user', parts: parts_(o)}],
    generationConfig: {responseMimeType: 'application/json', temperature: 0.4}
  });
  const t = (((r.candidates || [])[0] || {}).content || {parts: []}).parts.map(x => x.text || '').join('');
  try { return JSON.parse(t.replace(/^```(json)?|```$/g, '').trim()); }
  catch (e) { throw new Error('[gemini_error] Geminiの答えを読み取れませんでした'); }
}
function apiGeminiImage(o) {
  if (role_() !== 'hq') throw new Error('[permission_denied] 本社だけが使えます');
  const r = gemini_(PROPS_.getProperty('GEMINI_IMAGE_MODEL') || 'gemini-nano-banana-2.1', {
    contents: [{role: 'user', parts: parts_(o)}],
    generationConfig: {responseModalities: ['TEXT', 'IMAGE']}
  });
  const ps = (((r.candidates || [])[0] || {}).content || {parts: []}).parts || [];
  const img = ps.find(x => x.inlineData || x.inline_data);
  if (!img) {
    const why = ps.map(x => x.text || '').join(' ').slice(0, 200);
    throw new Error('[gemini_error] 画像が返ってきませんでした' + (why ? '：' + why : ''));
  }
  const d = img.inlineData || img.inline_data;
  log_('Gemini画像生成', '');
  return {mime: d.mimeType || d.mime_type || 'image/png', b64: d.data};
}
