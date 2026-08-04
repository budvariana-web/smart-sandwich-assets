/**
 * Smart Sandwich Bar - digital menu board backend.
 * Bind this script to the Google Spreadsheet (Extensions -> Apps Script).
 */
const CONFIG = Object.freeze({
  MENU_SHEET_NAME: 'MENU',
  MENU_SHEET_ME: 'MENU_ME',
  DEFAULT_BRAND: 'SMART SANDWICH BAR',
  DEFAULT_LANG: 'ru',
  DEFAULT_REFRESH_SECONDS: 60,
  MAX_REFRESH_SECONDS: 600,
  BUILD_ID: '%%BUILD_ID%%',
  GITHUB_ASSETS_BASE: 'https://budvariana-web.github.io/smart-sandwich-assets/assets/',
  FALLBACK_VIDEO_URLS: [
    'https://budvariana-web.github.io/smart-sandwich-assets/assets/videos/video_9c3d99d89a14.mp4',
    'https://budvariana-web.github.io/smart-sandwich-assets/assets/videos/video_782087e05f39.mp4'
  ]
});

/**
 * Resolve display language: 'me' (crnogorski), 'ru' (default) or 'both' (merged:
 * 3 RU dishes, then the same 3 ME dishes, alternating).
 * Priority: URL param ?lang=... > SETTINGS 'Язык' > DEFAULT_LANG.
 */
function resolveLang_(e) {
  var urlLang = (e && e.parameter && e.parameter.lang) ? String(e.parameter.lang).toLowerCase() : '';
  if (urlLang === 'both' || urlLang === 'mix' || urlLang === 'mixed' || urlLang === 'ru-me' || urlLang === 'me-ru' || urlLang === 'bi' || urlLang === 'bilingual') return 'both';
  if (urlLang === 'me' || urlLang === 'sr' || urlLang === 'cnr' || urlLang === 'cg') return 'me';
  if (urlLang === 'ru' || urlLang === 'rus') return 'ru';
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var settingsSheet = ss.getSheetByName('SETTINGS');
  if (settingsSheet) {
    var sd = settingsSheet.getDataRange().getValues();
    for (var r = 1; r < sd.length; r++) {
      var key = normalize_(String(sd[r][0])).toLowerCase();
      if (key === 'язык' || key === 'lang' || key === 'language') {
        var val = normalize_(String(sd[r][1])).toLowerCase();
        if (val === 'both' || val === 'mix' || val === 'mixed' || val === 'ru-me' || val === 'me-ru') return 'both';
        if (val.indexOf('me') === 0 || val === 'cnr' || val === 'cg') return 'me';
        if (val === 'ru' || val === 'rus') return 'ru';
      }
    }
  }
  return CONFIG.DEFAULT_LANG;
}

function doGet(e) {
  var param = (e && e.parameter && e.parameter.page) || '';
  var lang = resolveLang_(e);
  if (param === 'data') {
    return ContentService.createTextOutput(JSON.stringify(readMenuItems_(lang)))
      .setMimeType(ContentService.MimeType.JSON);
  }
  var t = HtmlService.createTemplateFromFile('Index');
  t.lang = lang;
  return t.evaluate()
    .setTitle('Smart Sandwich Bar - menu')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function doPost(e) { return doGet(e); }

function getData(lang) { return readMenuItems_(lang); }

function include_(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function safeImageUrl_(url) {
  if (!url) return '';
  if (url.indexOf('asset:') === 0) {
    var id = url.slice(6);
    return CONFIG.GITHUB_ASSETS_BASE + 'images/' + id + '.jpg';
  }
  if (url.indexOf('https://') === 0) return url;
  return '';
}

var FALLBACK_IMAGES = {
  '\u0427\u0435\u0434\u0434\u0435\u0440 BBQ': 'cheddar-bbq.jpg',
  '\u041a\u0443\u0440\u0438\u043d\u044b\u0439 \u0441\u043f\u0430\u0439\u0441\u0438': 'chicken-spicy.jpg',
  '\u0418\u043d\u0434\u0435\u0439\u043a\u0430 BBQ': 'turkey-bbq.jpg',
  '\u041f\u0435\u0441\u0442\u043e \u043c\u043e\u0446\u0430\u0440\u0435\u043b\u043b\u0430': 'pesto-mozzarella.jpg',
  '\u041a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c \u0444\u0440\u0438': 'fries.jpg',
  '\u041b\u0438\u043c\u043e\u043d\u0430\u0434': 'lemonade.jpg',
  '\u0410\u043c\u0435\u0440\u0438\u043a\u0430\u043d\u043e': 'americano.jpg'
};

function normalize_(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

/* === ANNOUNCEMENTS === */
function readAnnouncements_(lang) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var names = (lang === 'me')
    ? ['OBAVE_ME', 'ОБЈАВЕ_МЕ', 'ОБЈАВЕ', 'ANNOUNCEMENTS_ME', 'OBAVE']
    : ['ОБЪЯВЛЕНИЯ', 'ANNOUNCEMENTS', 'Объявления', 'Announcements'];
  var sheet = null;
  for (var i = 0; i < names.length; i++) {
    sheet = ss.getSheetByName(names[i]);
    if (sheet) break;
  }
  if (!sheet) {
    try {
      sheet = ss.insertSheet(lang === 'me' ? 'OBAVE_ME' : 'ОБЪЯВЛЕНИЯ');
      sheet.getRange(1, 1).setValue(lang === 'me' ? 'Objava' : 'Объявление');
    } catch (err) {
      return [];
    }
  }
  var data = sheet.getDataRange().getValues();
  var out = [];
  var start = 0;
  if (data.length > 0) {
    var first = normalize_(String(data[0][0])).toLowerCase();
    if (first.indexOf('объявл') === 0 || first.indexOf('announcement') === 0 || first.indexOf('objav') === 0) start = 1;
  }
  for (var r = start; r < data.length; r++) {
    var txt = normalize_(String(data[r][0]));
    if (txt) out.push(txt);
  }
  return out;
}

function parseVideoUrls_(val) {
  if (!val) return [];
  return val.split(/[,;\n]+/)
    .map(function(s) { return s.trim(); })
    .filter(function(s) { return s.length > 0; })
    .map(function(s) {
      // If it's just a filename, map to GitHub
      if (s.indexOf('http') !== 0) {
        return CONFIG.GITHUB_ASSETS_BASE + 'videos/' + s;
      }
      return s;
    });
}

function readItemsFromSheet_(menuSheet) {
  var data = menuSheet.getDataRange().getValues();
  if (data.length < 2) return [];
  var headers = data[0].map(function(h) { return normalize_(String(h)).toLowerCase(); });
  var items = [];
  for (var r = 1; r < data.length; r++) {
    var row = data[r];
    var obj = {};
    headers.forEach(function(h, c) { if (h) obj[h] = row[c]; });
    var name = normalize_(obj['название'] || obj['name'] || '');
    if (!name) continue;
    // Visibility checkbox (K 'Показывать'): explicitly FALSE hides the item.
    // Empty or TRUE shows it (backward compatible with pre-checkbox rows).
    var showRaw = obj['показывать'] || obj['show'] || obj['отображать'] || '';
    if (showRaw === false || String(showRaw).toLowerCase() === 'false') continue;
    // Description precedence: 'Описание наше' (J) wins, else 'Описание i-food' (C),
    // else legacy 'Описание' (pre-split sheets).
    var descOurs = normalize_(obj['описание наше'] || obj['наше описание'] || obj['описание своё'] || '');
    var descIfood = normalize_(obj['описание i-food'] || obj['описание ifood'] || obj['описание'] || obj['description'] || '');
    items.push({
      name: name,
      category: normalize_(obj['категория'] || obj['category'] || ''),
      price: normalize_(obj['цена'] || obj['price'] || ''),
      oldPrice: normalize_(obj['старая цена'] || obj['old price'] || ''),
      description: descOurs || descIfood,
      badge: normalize_(obj['бейдж'] || obj['badge'] || ''),
      orderKey: normalize_(obj['порядок'] || obj['order'] || obj['sort'] || ''),
      imageUrl: safeImageUrl_(obj['фото'] || obj['photo'] || obj['image'] || '') || (FALLBACK_IMAGES[name] ? CONFIG.GITHUB_ASSETS_BASE + 'images/' + FALLBACK_IMAGES[name] : '')
    });
  }
  return items;
}

function readMenuItems_(lang) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var settingsSheet = ss.getSheetByName('SETTINGS');
  var items = [];
  var sourceName = '';
  if (lang === 'both') {
    // Merged mode: 3 RU dishes, then the SAME 3 ME dishes, then next 3 RU, etc.
    var ruSheet = ss.getSheetByName(CONFIG.MENU_SHEET_NAME);
    var meSheet = ss.getSheetByName(CONFIG.MENU_SHEET_ME);
    var ruItems = ruSheet ? readItemsFromSheet_(ruSheet) : [];
    var meItems = meSheet ? readItemsFromSheet_(meSheet) : [];
    // Pair by order key (same dish in both languages), fallback to index.
    var meByKey = {};
    meItems.forEach(function(m, idx) { if (m.orderKey) meByKey[m.orderKey] = m; else meByKey['idx' + idx] = m; });
    var CHUNK = 3;
    for (var i = 0; i < ruItems.length; i += CHUNK) {
      for (var j = i; j < Math.min(i + CHUNK, ruItems.length); j++) items.push(ruItems[j]);
      for (var j2 = i; j2 < Math.min(i + CHUNK, ruItems.length); j2++) {
        var meItem = (ruItems[j2].orderKey && meByKey[ruItems[j2].orderKey]) ? meByKey[ruItems[j2].orderKey] : meItems[j2];
        if (meItem) items.push(meItem);
      }
    }
    // Any ME items without a RU counterpart at the end
    for (var k = 0; k < meItems.length; k++) {
      var isPaired = false;
      for (var p = 0; p < ruItems.length && !isPaired; p++) {
        if (ruItems[p].orderKey && meItems[k].orderKey && ruItems[p].orderKey === meItems[k].orderKey) isPaired = true;
        if (!ruItems[p].orderKey && !meItems[k].orderKey && p === k) isPaired = true;
      }
      if (!isPaired) items.push(meItems[k]);
    }
    sourceName = (ruSheet ? ruSheet.getName() : '') + ' + ' + (meSheet ? meSheet.getName() : '');
  } else {
    var sheetName = (lang === 'me') ? CONFIG.MENU_SHEET_ME : CONFIG.MENU_SHEET_NAME;
    var menuSheet = ss.getSheetByName(sheetName) || ss.getSheetByName(CONFIG.MENU_SHEET_NAME);
    if (!menuSheet) return { items: [], brand: CONFIG.DEFAULT_BRAND, lang: lang };
    items = readItemsFromSheet_(menuSheet);
    sourceName = menuSheet.getName();
  }
  var brand = CONFIG.DEFAULT_BRAND;
  var refreshSec = CONFIG.DEFAULT_REFRESH_SECONDS;
  var pageSec = 15;
  var videoSec = 10;
  var annSec = 8;
  var videoUrls = [];
  if (settingsSheet) {
    var sd = settingsSheet.getDataRange().getValues();
    for (var r = 1; r < sd.length; r++) {
      var key = normalize_(String(sd[r][0])).toLowerCase();
      var val = normalize_(String(sd[r][1]));
      if (!key || !val) continue;
      if (key === 'название' || key === 'brand') brand = val;
      if (key === 'обновление (сек)' || key === 'refresh') refreshSec = Math.min(parseInt(val) || 60, CONFIG.MAX_REFRESH_SECONDS);
      if (key === 'перелистывание (сек)' || key === 'page') pageSec = parseInt(val) || 15;
      if (key === 'видео интервал (сек)' || key === 'video seconds') videoSec = parseInt(val) || 10;
      if (key === 'объявления (сек)' || key === 'announcements seconds') annSec = parseInt(val) || 8;
      if (key === 'video_urls' || key === 'видео urls' || key === 'video' || key === 'видео') {
        videoUrls = parseVideoUrls_(val);
      }
    }
  }
  // Fallback to config videos if no URLs from sheet
  if (videoUrls.length === 0) {
    videoUrls = CONFIG.FALLBACK_VIDEO_URLS;
  }
  return {
    items: items, brand: brand,
    refreshSeconds: refreshSec, pageSeconds: pageSec, videoSeconds: videoSec,
    announcements: readAnnouncements_(lang === 'both' ? 'ru' : lang), announcementSeconds: annSec,
    videoUrls: videoUrls, buildId: CONFIG.BUILD_ID,
    sourceSheet: sourceName, lang: lang
  };
}

function getMenu() { return readMenuItems_(resolveLang_(null)); }
