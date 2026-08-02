# -*- coding: utf-8 -*-
"""Create MENU_ME (crnogorski) + OBAVE_ME sheets in the Smart Sandwich Bar spreadsheet.
Copies structure of MENU, translates names/descriptions, keeps prices/photos/order.
"""
import json, time, urllib.request, urllib.parse, base64, sys

SA_PATH = r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\.credentials\service-account.json'
SPREADSHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'

SA = json.load(open(SA_PATH, encoding='utf-8'))
def b64url(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
now = int(time.time())
header = {"alg": "RS256", "typ": "JWT"}
claims = {"iss": SA["client_email"], "scope": "https://www.googleapis.com/auth/spreadsheets",
          "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
def sign(blob, key):
    key = serialization.load_pem_private_key(key, password=None)
    return key.sign(blob, padding.PKCS1v15(), hashes.SHA256())
seg = b64url(json.dumps(header).encode()) + '.' + b64url(json.dumps(claims).encode())
sig = b64url(sign(seg.encode(), SA['private_key'].encode()))
jwt = seg + '.' + sig
data = urllib.parse.urlencode({'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': jwt}).encode()
req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
tok = json.loads(urllib.request.urlopen(req).read())['access_token']

def api(url, method='GET', body=None):
    req = urllib.request.Request(url, method=method, headers={'Authorization': 'Bearer ' + tok})
    if body is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(body).encode()
    return json.loads(urllib.request.urlopen(req).read())

BASE = f'https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}'

# ---- Translation dictionary: (category_ru, name_ru) -> (cat_me, name_me, desc_ours_me, desc_ifood_me) ----
# desc_ours_me: translation of "Описание наше" (J), desc_ifood_me: translation of "Описание i-food" (C)
# Empty string means "keep original empty". 'SAME' means copy original.
T = {}

def t(cat, name, cat_me, name_me, ours=None, ifood=None):
    T[(cat, name)] = (cat_me, name_me, ours, ifood)

t('Бургеры', 'МАЧО БУРГЕР', 'Burgeri', 'MAČO BURGER',
  ours='Crna brioš peciva (pečemo sami), autorski sos sa blagom ljutinom, goveđa pljeskavica (samo meso i začini), sir čedar, karamelizovani luk, svježi paradajz, listovi salate.',
  ifood='Goveđa pljeskavica (samo meso i začini i ništa više), sir čedar, karamelizovani luk, svježi paradajz, listovi salate.')
t('Бургеры', 'БЕЛЛА БУРГЕР', 'Burgeri', 'BELA BURGER',
  ours='Roze brioš pecivo (pečemo sami), ajoli sos (hand made) + francuski senf. Pileća pljeskavica (samo meso i začini i ništa više), sir čedar, karamelizovani luk, svježi paradajz, listovi salate.',
  ifood='Roze brioš pecivo (pečemo sami), ajoli sos (hand made) + francuski senf. Pileća pljeskavica (samo meso i začini i ništa više), sir čedar, karamelizovani luk, svježi paradajz, listovi salate.')
t('Бургеры', 'Сет «Белла Бургер»: бургер, фри, соус', 'Burgeri', 'Set «Bela Burger»: burger, pomfrit, sos',
  ours='', ifood='Burger u roze brioš pecivu sa piletinom 400 g, pomfrit 150 g i sos po izboru: ajoli, kečap, kečap sa čili sosom.')
t('Бургеры', 'Сет МАЧО БУРГЕР: бургер, фри, соус', 'Burgeri', 'Set MAČO BURGER: burger, pomfrit, sos',
  ours='Crni MAČO burger sa govedinom, pomfrit sa dimljenom paprikom i sos po izboru: kečap, kečap sa čili ili ajoli sa francuskim senfom (hand made).',
  ifood='')
t('Сэндвичи', 'Сэндвич «Неаполитано»', 'Sendviči', 'Sendvič «Napolitano»',
  ours='', ifood='Ciabatta (pečemo sami), pesto sos, italijanska mortadela, mocarela, sušeni paradajz. Prije serviranja sendvič se zagrijava u pres grilu do hrskave korice.')
t('Сэндвичи', 'Сэндвич «Украинский вайб»', 'Sendviči', 'Sendvič «Ukrajinski vajb»',
  ours='', ifood='Ciabatta (pečemo sami), pečena svinjetina (ne masna) sa bijelim lukom i začinima, kiseli krastavac, kiseli crveni luk, ajoli sa francuskim senfom, kečap, barbekju sos. Po vašoj želji možemo dodati')
t('Сэндвичи', 'Сэндвич «Неаполитано Плюс»', 'Sendviči', 'Sendvič «Napolitano Plus»',
  ours='', ifood='Sendvič od tanke fokače, i još više nadjeva. Fokača začinjena parmezanom i italijanskim začinskim biljem. Hrskava korica! Nadjev od italijanske mortadele, pesto sosa, mocarele, sušenog paradajza, bosiljka i svježe')
t('Сэндвичи', 'Сэндвич «Монтенегро Лав»', 'Sendviči', 'Sendvič «Montenegro Lav»',
  ours='', ifood='Klasičan ukus Crne Gore. Njeguški sušeni pršut, sir edamer, svježi krastavac i sos na bazi kečapa, majoneza, senfa i kiselih krastavčića.')
t('Сэндвичи', 'Сэндвич с курицей по-каталонски', 'Sendviči', 'Sendvič sa piletinom na katalonski način',
  ours='', ifood='Pileći bataci prvo se mariniraju u crvenom vinu uz dodatak kapara i maslina, bijelog luka i luka. Peče se u rerni i reže. Servira se na ciabatti ili fokači sa sosom na bazi maslina, sa svježim paradajzom')
t('Сэндвичи', 'Сэндвич с салями', 'Sendviči', 'Sendvič sa salamom',
  ours='Ciabatta (pečemo sami), italijanska salama, svježi paradajz, listovi salate i sos po izboru. Zagrijava se u pres grilu do hrskave korice.',
  ifood='')
t('Брускеты', 'Брускетта с карамелизированным луком и пршутом', 'Bruskete', 'Brusketa sa karamelizovanim lukom i pršutom',
  ours='Hrskav prepečeni hljeb, karamelizovani luk i nježni pršut.', ifood='')
t('Брускеты', 'Брускета с черри, маслинами и салями', 'Bruskete', 'Brusketa sa čeri paradajzom, maslinama i salamom',
  ours='Hrskav prepečeni hljeb sa čeri paradajzom, maslinama i salamom.', ifood='')
t('Фокачча', 'Фокачча с маслинами и сыром', 'Fokača', 'Fokača sa maslinama i sirom',
  ours='Domaća fokača (pečemo sami) sa maslinama i sirom. Cijela fokača — kao predjelo ili osnova za sendvič.', ifood='')
t('Закуски', 'Аранчини', 'Predjela', 'Arancini',
  ours='Arancini su sicilijanska brza hrana. Kugla od pirinča u prezlima, pržena u fritezi, sa nadjevom od mesnog ragu-a, zelenog graška i mocarele. Težina svake kugle 220 grama.', ifood='')
t('Закуски', 'Чесночные гренки из ржаного хлеба', 'Predjela', 'Bjelolučni krutoni od ražanog hljeba',
  ours='Sami pečemo crni ražani hljeb sa sladom. Pravimo krutone u fritezi uz dodatak konfita od bijelog luka.', ifood='')
t('Закуски', 'Сет: гренки + 3 соуса', 'Predjela', 'Set: krutoni + 3 sosa',
  ours='Uz bjelolučne krutone od ražanog hljeba dodali smo tri sosa: ajoli, karamelizovani luk i, za još veću ljutinu, sos Marinado od maslinovog ulja, bijelog luka i zeleni.', ifood='')
t('Закуски', 'Картофель фри', 'Predjela', 'Pomfrit',
  ours='Zlatni pomfrit (150 g). Servira se sa sosom po izboru: kečap, kečap sa čili ili ajoli.', ifood='')
t('Хлеб', 'Чиабатта', 'Hljeb', 'Ciabatta',
  ours='Ciabatta je italijanski hljeb koji sami pečemo i sa njim pravimo sendviče.', ifood='')
t('Десерты', 'Апельсиновый кекс «Таормина»', 'Dezerti', 'Pomorandžin kolač «Taormina»',
  ours='U sastavu kolača su samo prirodni proizvodi: pomorandže, biljno ulje, jaja i brašno. Ukus Sicilije u svakom zalogaju.', ifood='')
t('Соусы', 'Карамелизированный лук', 'Umaci', 'Karamelizovani luk',
  ours='Slatki dinstani luk — idealan dodatak burgerima, krutonima i sendvičima.', ifood='')
t('Соусы', 'Айоли', 'Umaci', 'Ajoli',
  ours='Domaći ajoli sos (hand made) sa francuskim senfom — uz burgere, pomfrit i krutone.', ifood='')
t('Соусы', 'Острый кетчуп', 'Umaci', 'Ljuti kečap',
  ours='Kečap sa čilijem — pikantna ljutina za burgere, pomfrit i krutone.', ifood='')
t('Соусы', 'Кетчуп', 'Umaci', 'Kečap',
  ours='Klasični kečap — uz burgere, pomfrit i krutone.', ifood='')
t('Напитки', 'Лимонад', 'Pića', 'Limunada',
  ours='Domaća, 0,4 l', ifood='')
t('Напитки', 'Американо', 'Pića', 'Amerikano',
  ours='Klasična crna kafa', ifood='')

ANNOUNCEMENTS_ME = [
    'Objava',
    'Popust 10% na sve burgere utorkom!',
    'Novi sendvič Napolitano — probaj danas',
    'Kafa za ponijeti — 2 eura, besplatni sirup',
    'Doručak do 12:00: burger + limunada za 7 eura',
]

# ---- Read source MENU ----
vals = api(f'{BASE}/values/MENU')['values']
headers = vals[0]
rows = vals[1:]
vis = [r for r in rows if len(r) > 10 and r[10].strip().lower() == 'true' and len(r) > 5 and r[5] == 'Да']
vis.sort(key=lambda r: int(r[6]) if r[6].strip().isdigit() else 999)
print('Source MENU rows:', len(rows), '| visible:', len(vis))

out_rows = [headers]
missing = []
for r in vis:
    cat, name = r[0], r[1]
    key = (cat, name)
    if key not in T:
        missing.append(key)
        continue
    cat_me, name_me, ours_me, ifood_me = T[key]
    new = list(r)
    new[0] = cat_me
    new[1] = name_me
    if len(new) > 2:
        # C = Описание i-food
        src_ifood = new[2] if len(new) > 2 else ''
        new[2] = ifood_me if (src_ifood and ifood_me) else (src_ifood if src_ifood and ifood_me is None else (ifood_me if ifood_me is not None else src_ifood))
    if len(new) > 5:
        new[5] = 'Da'
    if len(new) > 9:
        src_ours = new[9]
        new[9] = ours_me if (src_ours and ours_me) else (ours_me if ours_me is not None else src_ours)
    out_rows.append(new)

if missing:
    print('MISSING translations:', missing)
    sys.exit(1)

print('Translated items:', len(out_rows) - 1)

# ---- Create MENU_ME sheet ----
existing = {s['properties']['title'] for s in api(f'{BASE}?fields=sheets(properties.title)')['sheets']}
def ensure_sheet(title):
    if title in existing:
        print(f'Sheet {title} exists')
        return
    api(f'{BASE}:batchUpdate', method='POST', body={
        'requests': [{'addSheet': {'properties': {'title': title}}}]
    })
    print(f'Sheet {title} created')

ensure_sheet('MENU_ME')
ensure_sheet('OBAVE_ME')

# ---- Write MENU_ME ----
def write_values(sheet, values):
    body = {'values': values}
    url = f'{BASE}/values/{urllib.parse.quote(sheet)}!A1:K{len(values)}?valueInputOption=RAW'
    api(url, method='PUT', body=body)
    print(f'{sheet}: wrote {len(values)} rows')

write_values('MENU_ME', out_rows)
write_values('OBAVE_ME', [[a] for a in ANNOUNCEMENTS_ME])

# ---- Add "Язык" setting if missing ----
sv = api(f'{BASE}/values/SETTINGS')['values']
has_lang = any(str(r[0]).strip().lower() in ('язык', 'lang') for r in sv if r)
if not has_lang:
    sv.append(['Язык', 'ru'])
    api(f'{BASE}/values/SETTINGS!A1:B{len(sv)}?valueInputOption=RAW', method='PUT', body={'values': sv})
    print('SETTINGS: added Язык=ru')
else:
    print('SETTINGS: Язык already present')

print('DONE')
