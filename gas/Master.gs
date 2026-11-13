/**
 * 原価マスターの初期値（setup が master/defaults に書き込む）
 * 数字は空欄のままです。設置後、本社の「原価マスター」画面で入力してください。
 */
const MASTER_DEFAULTS = {
 "margin": "",
 "tax": 0.1,
 "unit": 1000,
 "round": "切捨て",
 "validDays": null,
 "leadMax": 90,
 "rateDate": "",
 "depositRate": 0.5,
 "depositUnit": 1000,
 "marginAlert": "",
 "metals": {
  "K10YG": {
   "cls": "K10",
   "dens": 11.6,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 14929029,
   "lbl": "10金イエローゴールド"
  },
  "K10PG": {
   "cls": "K10",
   "dens": 11.6,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 15252636,
   "lbl": "10金ピンクゴールド"
  },
  "K10WG": {
   "cls": "K10",
   "dens": 11.9,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 15329770,
   "lbl": "10金ホワイトゴールド",
   "rh": true
  },
  "K18YG": {
   "cls": "K18",
   "dens": 15.5,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 15123034,
   "lbl": "18金イエローゴールド"
  },
  "K18PG": {
   "cls": "K18",
   "dens": 15.2,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 15183500,
   "lbl": "18金ピンクゴールド"
  },
  "K18WG": {
   "cls": "K18",
   "dens": 15.8,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 15592942,
   "lbl": "18金ホワイトゴールド",
   "rh": true
  },
  "Pt950": {
   "cls": "Pt",
   "dens": 20.6,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 14343392,
   "lbl": "プラチナ950"
  },
  "Pt900": {
   "cls": "Pt",
   "dens": 20,
   "g": "",
   "gs": "tmp",
   "loss": "",
   "col": 14080220,
   "lbl": "プラチナ900"
  }
 },
 "cad": [
  "",
  "",
  "",
  ""
 ],
 "print": [
  "",
  "",
  "",
  ""
 ],
 "finish": [
  "",
  "",
  "",
  ""
 ],
 "castSTL": [],
 "set": {
  "s_ind": "",
  "s_sh": "",
  "m_ind": "",
  "m_sh": "",
  "c46": "",
  "c6": "",
  "hori": "",
  "bezS": "",
  "bezM": "",
  "rail": ""
 },
 "assembly": "",
 "braze": "",
 "rh": {
  "ring": "",
  "pendant": "",
  "pierce": ""
 },
 "stamp": "",
 "inspect": "",
 "grades": [
  "H-I / SI",
  "F-G / VS",
  "D-E / VVS"
 ],
 "center": [
  [
   0.1,
   [
    "",
    "",
    ""
   ]
  ],
  [
   0.2,
   [
    "",
    "",
    ""
   ]
  ],
  [
   0.3,
   [
    "",
    "",
    ""
   ]
  ],
  [
   0.4,
   [
    "",
    "",
    ""
   ]
  ],
  [
   0.5,
   [
    "",
    "",
    ""
   ]
  ],
  [
   0.7,
   [
    "",
    "",
    ""
   ]
  ],
  [
   1,
   [
    "",
    "",
    ""
   ]
  ],
  [
   1.5,
   [
    "",
    "",
    ""
   ]
  ]
 ],
 "centerSrc": "tmp",
 "sides": [
  {
   "id": "d08",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 0.8,
   "ct": 0.0025,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d09",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 0.9,
   "ct": 0.003,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d1",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1,
   "ct": 0.005,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d11",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.1,
   "ct": 0.006,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d12",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.2,
   "ct": 0.008,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d13",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.3,
   "ct": 0.01,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d14",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.4,
   "ct": 0.012,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d15",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.5,
   "ct": 0.015,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d17",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.7,
   "ct": 0.02,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d18",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 1.8,
   "ct": 0.025,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d2",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 2,
   "ct": 0.03,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d22",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 2.2,
   "ct": 0.04,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d25",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 2.5,
   "ct": 0.06,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d27",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 2.7,
   "ct": 0.08,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "d3",
   "kind": "dia",
   "name": "メレダイヤ",
   "grade": "H/SI/GDup",
   "mm": 3,
   "ct": 0.1,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c0",
   "kind": "color",
   "name": "アメジスト",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c1",
   "kind": "color",
   "name": "ローズアメジスト",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c2",
   "kind": "color",
   "name": "ピンクトルマリン",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c3",
   "kind": "color",
   "name": "ガーネット",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c4",
   "kind": "color",
   "name": "ペリドット",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c5",
   "kind": "color",
   "name": "グリーンガーネット",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c6",
   "kind": "color",
   "name": "グリーントルマリン",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c7",
   "kind": "color",
   "name": "アクアマリン",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c8",
   "kind": "color",
   "name": "スカイブルートパーズ",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c9",
   "kind": "color",
   "name": "スイスブルートパーズ",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c10",
   "kind": "color",
   "name": "ロンドンブルートパーズ",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c11",
   "kind": "color",
   "name": "ホワイトトパーズ",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c12",
   "kind": "color",
   "name": "シトリン",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c13",
   "kind": "color",
   "name": "マンダリンガーネット",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  },
  {
   "id": "c14",
   "kind": "color",
   "name": "タンザナイト",
   "grade": "",
   "mm": 2,
   "ct": 0.035,
   "pc": "",
   "src": "fix",
   "ctSrc": "tmp"
  }
 ],
 "parts": {
  "post": {
   "n": "ピアスポスト＋キャッチ（ペア）",
   "K10": "",
   "K18": "",
   "Pt": "",
   "s": "tmp"
  },
  "chain20": {
   "n": "チェーン アズキ0.20 No.2 45cm",
   "K10": "",
   "K18": "",
   "Pt": "",
   "s": "tmp"
  },
  "chain25": {
   "n": "チェーン アズキ0.25 40cm",
   "K10": "",
   "K18": "",
   "Pt": "",
   "s": "tmp"
  },
  "chain30": {
   "n": "チェーン アズキ0.30 40cm",
   "K10": "",
   "K18": "",
   "Pt": "",
   "s": "tmp"
  },
  "clasp": {
   "n": "6mm 引輪＋ダルマプレート",
   "K10": "",
   "K18": "",
   "Pt": "",
   "s": "tmp"
  }
 },
 "tex": {
  "サテン": null,
  "槌目": null,
  "コンビ": null
 },
 "extras": {
  "box": {
   "n": "ケース・箱",
   "v": null,
   "inc": false
  },
  "cert": {
   "n": "保証書",
   "v": null,
   "inc": false
  },
  "ship": {
   "n": "工場往復送料",
   "v": null,
   "inc": false
  },
  "csFee": {
   "n": "お預り石 取扱料（1石）",
   "v": null
  }
 },
 "calib": {},
 "lead": {
  "cad": 7,
  "check": 3,
  "print": 3,
  "cast": 7,
  "buy": 14,
  "consign": 5,
  "stock": 2,
  "setting": 7,
  "finish": 5,
  "ship": 3
 }
};
