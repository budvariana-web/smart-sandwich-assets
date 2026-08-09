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

function localizedText_(obj, lang) {
  // `headers` is normalized to lower-case in readItemsFromSheet_, so language
  // suffixes must be lower-case too: 'название (me)', not '(ME)'.
  var suffix = lang === 'ru' ? '' : ' (' + lang + ')';
  var description = lang === 'ru'
    ? normalize_(obj['описание наше'] || obj['наше описание'] || obj['описание своё'] || obj['описание i-food'] || obj['описание ifood'] || obj['описание'] || '')
    : normalize_(obj['описание' + suffix] || '');
  return {
    category: normalize_(obj['категория' + suffix] || (lang === 'ru' ? obj['категория'] : '') || ''),
    name: normalize_(obj['название' + suffix] || (lang === 'ru' ? obj['название'] || obj['name'] : '') || ''),
    description: description
  };
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
    var ru = localizedText_(obj, 'ru');
    if (!ru.name) continue;
    // Visibility checkbox: explicitly FALSE hides the item. Do not replace this
    // with `||`: boolean false is a valid Sheets checkbox value.
    var showRaw = Object.prototype.hasOwnProperty.call(obj, 'показывать') ? obj['показывать'] : '';
    if (showRaw === false || String(showRaw).toLowerCase() === 'false') continue;
    var languages = {ru: ru, me: localizedText_(obj, 'me'), en: localizedText_(obj, 'en'), de: localizedText_(obj, 'de')};
    items.push({
      languages: languages,
      // Keep RU flat fields for API clients using ?lang=ru during the transition.
      name: ru.name, category: ru.category, description: ru.description,
      price: normalize_(obj['цена'] || obj['price'] || ''),
      oldPrice: normalize_(obj['старая цена'] || obj['old price'] || ''),
      badge: normalize_(obj['бейдж'] || obj['badge'] || ''),
      orderKey: normalize_(obj['порядок'] || obj['order'] || obj['sort'] || ''),
      imageUrl: safeImageUrl_(obj['фото'] || obj['photo'] || obj['image'] || '') || (FALLBACK_IMAGES[ru.name] ? CONFIG.GITHUB_ASSETS_BASE + 'images/' + FALLBACK_IMAGES[ru.name] : '')
    });
  }
  return items;
}

function readMenuItems_(lang) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var settingsSheet = ss.getSheetByName('SETTINGS');
  var menuSheet = ss.getSheetByName(CONFIG.MENU_SHEET_NAME);
  if (!menuSheet) return {items: [], brand: CONFIG.DEFAULT_BRAND, lang: lang};
  var items = readItemsFromSheet_(menuSheet);
  var brand = CONFIG.DEFAULT_BRAND;
  var refreshSec = CONFIG.DEFAULT_REFRESH_SECONDS;
  var pageSec = 15;
  var videoSec = 10;
  var annSec = 8;
  var videoUrls = [];
  var showCategories = true;
  var bundlesBeforeVideo = 3;
  if (settingsSheet) {
    var sd = settingsSheet.getDataRange().getValues();
    for (var r = 1; r < sd.length; r++) {
      var key = normalize_(String(sd[r][0])).toLowerCase();
      var raw = sd[r][1];
      var val = normalize_(String(raw));
      if (!key) continue;
      if (key === 'бренд' || key === 'название' || key === 'brand') brand = val || brand;
      if (key === 'обновление сек' || key === 'обновление (сек)' || key === 'refresh') refreshSec = Math.min(parseInt(val, 10) || 60, CONFIG.MAX_REFRESH_SECONDS);
      if (key === 'перелистывание сек' || key === 'перелистывание (сек)' || key === 'page') pageSec = parseInt(val, 10) || 15;
      if (key === 'видео интервал (сек)' || key === 'video seconds') videoSec = parseInt(val, 10) || 10;
      if (key === 'объявления (сек)' || key === 'announcements seconds') annSec = parseInt(val, 10) || 8;
      if (key === 'показывать категории') showCategories = !(raw === false || String(raw).toLowerCase() === 'false');
      if (key === 'наборов до видео') bundlesBeforeVideo = Math.max(1, parseInt(val, 10) || 3);
      if (key === 'видео urls' || key === 'video_urls' || key === 'video' || key === 'видео') videoUrls = parseVideoUrls_(val);
    }
  }
  if (videoUrls.length === 0) videoUrls = CONFIG.FALLBACK_VIDEO_URLS;
  return {
    items: items, brand: brand,
    refreshSeconds: refreshSec, pageSeconds: pageSec, videoSeconds: videoSec,
    announcements: readAnnouncements_(lang === 'both' ? 'ru' : lang), announcementSeconds: annSec,
    videoUrls: videoUrls, buildId: CONFIG.BUILD_ID,
    sourceSheet: menuSheet.getName(), lang: lang,
    showCategories: showCategories, bundlesBeforeVideo: bundlesBeforeVideo
  };
}

function getMenu() { return readMenuItems_(resolveLang_(null)); }
