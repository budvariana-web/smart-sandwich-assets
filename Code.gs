/**
 * Smart Sandwich Bar - digital menu board backend.
 * Bind this script to the Google Spreadsheet (Extensions -> Apps Script).
 */
const CONFIG = Object.freeze({
  MENU_SHEET_NAME: 'MENU',
  DEFAULT_BRAND: 'SMART SANDWICH BAR',
  DEFAULT_REFRESH_SECONDS: 60,
  MAX_REFRESH_SECONDS: 600,
  BUILD_ID: '%%BUILD_ID%%',
  GITHUB_ASSETS_BASE: 'https://raw.githubusercontent.com/budvariana-web/smart-sandwich-assets/main/assets/',
  FALLBACK_VIDEO_URLS: [
    'https://raw.githubusercontent.com/budvariana-web/smart-sandwich-assets/main/assets/videos/video_9c3d99d89a14.mp4',
    'https://raw.githubusercontent.com/budvariana-web/smart-sandwich-assets/main/assets/videos/video_782087e05f39.mp4'
  ]
});

function doGet(e) {
  var param = (e && e.parameter && e.parameter.page) || '';
  if (param === 'data') {
    return ContentService.createTextOutput(JSON.stringify(readMenuItems_()))
      .setMimeType(ContentService.MimeType.JSON);
  }
  return HtmlService.createTemplateFromFile('Index').evaluate()
    .setTitle('Smart Sandwich Bar - menu')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function doPost(e) { return doGet(e); }

function getData() { return readMenuItems_(); }

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
function readAnnouncements_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var names = ['ОБЪЯВЛЕНИЯ', 'ANNOUNCEMENTS', 'Объявления', 'Announcements'];
  var sheet = null;
  for (var i = 0; i < names.length; i++) {
    sheet = ss.getSheetByName(names[i]);
    if (sheet) break;
  }
  if (!sheet) {
    try {
      sheet = ss.insertSheet('ОБЪЯВЛЕНИЯ');
      sheet.getRange(1, 1).setValue('Объявление');
    } catch (err) {
      return [];
    }
  }
  var data = sheet.getDataRange().getValues();
  var out = [];
  var start = 0;
  if (data.length > 0) {
    var first = normalize_(String(data[0][0])).toLowerCase();
    if (first.indexOf('объявл') === 0 || first.indexOf('announcement') === 0) start = 1;
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

function readMenuItems_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var menuSheet = ss.getSheetByName(CONFIG.MENU_SHEET_NAME) || ss.getSheets()[1];
  if (!menuSheet) return { items: [], brand: CONFIG.DEFAULT_BRAND };
  var settingsSheet = ss.getSheetByName('SETTINGS');
  var data = menuSheet.getDataRange().getValues();
  if (data.length < 2) return { items: [], brand: CONFIG.DEFAULT_BRAND };
  var headers = data[0].map(function(h) { return normalize_(String(h)).toLowerCase(); });
  var items = [];
  for (var r = 1; r < data.length; r++) {
    var row = data[r];
    var obj = {};
    headers.forEach(function(h, c) { if (h) obj[h] = row[c]; });
    var name = normalize_(obj['название'] || obj['name'] || '');
    if (!name) continue;
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
      imageUrl: safeImageUrl_(obj['фото'] || obj['photo'] || obj['image'] || '') || (FALLBACK_IMAGES[name] ? CONFIG.GITHUB_ASSETS_BASE + 'images/' + FALLBACK_IMAGES[name] : '')
    });
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
    announcements: readAnnouncements_(), announcementSeconds: annSec,
    videoUrls: videoUrls, buildId: CONFIG.BUILD_ID,
    sourceSheet: menuSheet.getName()
  };
}

function getMenu() { return readMenuItems_(); }
