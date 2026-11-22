const OPENING_WINDOWS = [[11 * 60, 15 * 60], [17 * 60, 22 * 60]];

function partsAt(date, timeZone) {
  const values = new Intl.DateTimeFormat('en-GB', {
    timeZone, weekday:'short', year:'numeric', month:'2-digit', day:'2-digit',
    hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'
  }).formatToParts(date).reduce((out, item) => ({ ...out, [item.type]: item.value }), {});
  return { year:+values.year, month:+values.month, day:+values.day, hour:+values.hour,
    minute:+values.minute, second:+values.second, weekday:values.weekday };
}
function offsetAt(date, timeZone) {
  const p = partsAt(date, timeZone);
  return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - date.getTime();
}
function instantForLocal(year, month, day, minute, timeZone) {
  const guess = new Date(Date.UTC(year, month - 1, day, Math.floor(minute / 60), minute % 60));
  let instant = new Date(guess.getTime() - offsetAt(guess, timeZone));
  instant = new Date(guess.getTime() - offsetAt(instant, timeZone));
  return instant;
}
function formatDuration(milliseconds) {
  const seconds = Math.max(0, Math.ceil(milliseconds / 1000));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map(value => String(value).padStart(2, '0')).join(':');
}
function formatHour(minute) { return `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`; }
function isServiceDay(year, month, day) {
  const weekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
  return weekday !== 1; // Tuesday through Sunday; Monday is closed.
}

export function getBarStatus(now = new Date(), timeZone = 'Europe/Podgorica') {
  const p = partsAt(now, timeZone);
  const todayMinute = p.hour * 60 + p.minute;
  if (isServiceDay(p.year, p.month, p.day)) {
    for (const [start, end] of OPENING_WINDOWS) {
      const startAt = instantForLocal(p.year, p.month, p.day, start, timeZone);
      const endAt = instantForLocal(p.year, p.month, p.day, end, timeZone);
      if (now < startAt) return { kind:'opens', label:'До открытия осталось:', value:formatDuration(startAt - now), nextOpen:formatHour(start) };
      if (now >= startAt && now < endAt) return { kind:'open', label:'Открыто до:', value:formatDuration(endAt - now), nextOpen:formatHour(end) };
    }
  }
  const cursor = new Date(Date.UTC(p.year, p.month - 1, p.day));
  for (let days = 1; days <= 8; days += 1) {
    cursor.setUTCDate(cursor.getUTCDate() + 1);
    if (!isServiceDay(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, cursor.getUTCDate())) continue;
    const opensAt = instantForLocal(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, cursor.getUTCDate(), OPENING_WINDOWS[0][0], timeZone);
    return { kind:'opens', label:'До открытия осталось:', value:formatDuration(opensAt - now), nextOpen:formatHour(OPENING_WINDOWS[0][0]) };
  }
  throw new Error('No next opening time found');
}
