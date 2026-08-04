import base64,json,time,urllib.parse,urllib.request
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
SHEET='1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
sa=json.load(open('.credentials/service-account.json',encoding='utf-8'))
def b64(v): return base64.urlsafe_b64encode(v).rstrip(b'=').decode()
now=int(time.time())
h=b64(json.dumps({'alg':'RS256','typ':'JWT'}).encode()); p=b64(json.dumps({'iss':sa['client_email'],'scope':'https://www.googleapis.com/auth/spreadsheets.readonly','aud':'https://oauth2.googleapis.com/token','iat':now,'exp':now+3600}).encode())
k=serialization.load_pem_private_key(sa['private_key'].encode(),None); jwt=h+'.'+p+'.'+b64(k.sign((h+'.'+p).encode(),padding.PKCS1v15(),hashes.SHA256()))
token=json.loads(urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode({'grant_type':'urn:ietf:params:oauth:grant-type:jwt-bearer','assertion':jwt}).encode())).read())['access_token']
for sheet in ['MENU','MENU_ME']:
 url='https://sheets.googleapis.com/v4/spreadsheets/'+SHEET+'/values/'+urllib.parse.quote(sheet+'!A1:K100',safe='!')+'?valueRenderOption=UNFORMATTED_VALUE'
 data=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token})).read()).get('values',[])
 header=data[0] if data else []
 rows=[]
 for n,row in enumerate(data[1:],2):
  if len(row)>1 and row[1]: rows.append({'row':n,'name':row[1],'K':row[10] if len(row)>10 else '<missing>'})
 print(json.dumps({'sheet':sheet,'header':header,'total':len(rows),'false':[x for x in rows if x['K'] is False or str(x['K']).lower()=='false'],'missingK':[x for x in rows if x['K']=='<missing>'],'sample':rows[:3]},ensure_ascii=False))