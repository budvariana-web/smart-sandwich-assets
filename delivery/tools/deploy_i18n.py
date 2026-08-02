# -*- coding: utf-8 -*-
"""Deploy smart-sandwich-menu-display to Apps Script: upload files -> new version -> update existing deployment."""
import json, time, urllib.request, urllib.parse, os, sys

BASE = r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar'
TOKEN_PATH = os.path.join(BASE, '.credentials', 'scripts-oauth-token.json')
CLIENT_PATH = os.path.join(BASE, '.credentials', 'client-secret.json')
SRC = os.path.join(BASE, 'delivery', 'smart-sandwich-menu-display')
SCRIPT_ID = '1ocvsaP1j5MPe3INWrUQmbSw0IT2ZOi-ZszAMeaDPoJgqLnjLBqvdzjJr'
DEPLOY_ID = 'AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg'

tok = json.load(open(TOKEN_PATH, encoding='utf-8'))
client = json.load(open(CLIENT_PATH, encoding='utf-8'))['installed']
data = urllib.parse.urlencode({
    'client_id': client['client_id'],
    'client_secret': client['client_secret'],
    'refresh_token': tok['refresh_token'],
    'grant_type': 'refresh_token'
}).encode()
req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
resp = json.loads(urllib.request.urlopen(req).read())
access = resp['access_token']
print('token ok')

def api(url, method='GET', body=None):
    req = urllib.request.Request(url, method=method, headers={'Authorization': 'Bearer ' + access})
    if body is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(body).encode()
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

build_id = 'menu-v60-i18n-' + time.strftime('%Y%m%d-%H%M%S')
def read(p):
    s = open(os.path.join(SRC, p), encoding='utf-8').read()
    return s.replace('%%BUILD_ID%%', build_id)

files = []
for name, typ in [('Code.gs', 'SERVER_JS'), ('Index.html', 'HTML'), ('Assets.html', 'HTML')]:
    files.append({'name': name, 'type': typ, 'source': read(name)})
manifest = open(os.path.join(SRC, 'appsscript.json'), encoding='utf-8').read()
files.append({'name': 'appsscript', 'type': 'JSON', 'source': manifest})

res = api(f'https://script.googleapis.com/v1/projects/{SCRIPT_ID}/content', method='PUT', body={'files': files})
print('uploaded files:', len(res.get('files', [])))

ver = api(f'https://script.googleapis.com/v1/projects/{SCRIPT_ID}/versions', method='POST',
          body={'description': 'i18n: crnogorski (ME) menu + lang switch'})
version_num = ver['versionNumber']
print('version:', version_num)

dep = api(f'https://script.googleapis.com/v1/projects/{SCRIPT_ID}/deployments/{DEPLOY_ID}', method='PUT',
          body={'deploymentConfig': {'versionNumber': version_num}})
print('deployment updated:', dep['deploymentId'])
print('URL: https://script.google.com/macros/s/%s/exec' % dep['deploymentId'])
