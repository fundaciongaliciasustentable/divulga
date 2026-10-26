import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
P={'2868':'A Coruña','2880':'Lugo','2885':'Ourense','2890':'Pontevedra'}
conc=[]
for t,prov in P.items():
    for x in json.load(open(HERE/f'data/ine_{t}.json')):
        md={m['T3_Variable']:m for m in x['MetaData']}
        if md.get('Sexo',{}).get('Nombre')!='Total': continue
        if 'Municipios' not in md: continue
        c=md['Municipios']['Codigo']
        if len(c)!=5 or not x['Data']: print('skip',md['Municipios']['Nombre']); continue
        conc.append({'id':c,'n':md['Municipios']['Nombre'],'p':prov,'v':int(x['Data'][0]['Valor']),'y':x['Data'][0]['Anyo']})
print(len(conc), sum(c['v'] for c in conc), {c['y'] for c in conc})
# nice Galician names from perfil
g=json.load(open('/Users/perezgulin/Proxectos/galicia-agora/data-out/perfil-concellos/data.geojson'))
names={f['properties']['codigo_ine']:f['properties']['nome'] for f in g['features']}
miss=[c for c in conc if c['id'] not in names]; print('missing',miss)
for c in conc: c['n']=names.get(c['id'],c['n'])
d=json.load(open(HERE/'data/pere_gal.json'))
tot=None; rows=[]
for x in d:
    nm=x['Nombre'].split('. Galicia')[0]; v=x['Data'][0]['Valor'] if x['Data'] else 0
    if nm.startswith('1. TOTAL'): tot=int(v); yr=x['Data'][0]['Anyo']; continue
    if 'TOTAL' in nm or nm.startswith('Resto') or not v: continue
    rows.append((nm,int(v)))
rows.sort(key=lambda r:-r[1])
GL={'Argentina':'Arxentina','Brasil':'Brasil','Cuba':'Cuba','Uruguay':'Uruguai','Suiza':'Suíza','Venezuela':'Venezuela','Estados Unidos de América':'EUA','Francia':'Francia','Alemania':'Alemaña','Reino Unido':'Reino Unido','México':'México','Portugal':'Portugal','Chile':'Chile','Panamá':'Panamá','Países Bajos':'Países Baixos','Bélgica':'Bélxica','República Dominicana':'Rep. Dominicana','Canadá':'Canadá','Andorra':'Andorra','Australia':'Australia','Italia':'Italia','Perú':'Perú','Colombia':'Colombia','Costa Rica':'Costa Rica','Irlanda':'Irlanda'}
ext=[{'id':'X'+str(i),'n':GL.get(n,n),'p':'Exterior','v':v} for i,(n,v) in enumerate(rows) if v>=1000]
otros=tot-sum(e['v'] for e in ext)
ext.append({'id':'Xoutros','n':'Outros países','p':'Exterior','v':otros})
print(tot,yr,len(ext),[ (e['n'],e['v']) for e in ext])
json.dump({'concellos':conc,'exterior':ext,'anoPadron':conc[0]['y'],'anoPERE':yr,'totalExterior':tot},open(HERE/'data/datos.json','w'),ensure_ascii=False)
