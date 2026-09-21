import json, urllib.request, re

SOURCES = [
 "https://raw.githubusercontent.com/ProxyScrape/free-proxy-list/main/proxies/countries/cn/data.json",
 "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies.json",
]
CITY = {
"Beijing":"北京","Jinrongjie":"北京","Shanghai":"上海","Tianjin":"天津","Chongqing":"重庆",
"Guangzhou":"广东-广州","Shenzhen":"广东-深圳","Dongguan":"广东-东莞","Foshan":"广东-佛山",
"Hangzhou":"浙江-杭州","Ningbo":"浙江-宁波","Wenzhou":"浙江-温州",
"Nanjing":"江苏-南京","Suzhou":"江苏-苏州","Wuxi":"江苏-无锡",
"Jinan":"山东-济南","Qingdao":"山东-青岛","Zhengzhou":"河南-郑州","Shijiazhuang":"河北-石家庄",
"Wuhan":"湖北-武汉","Changsha":"湖南-长沙","Hefei":"安徽-合肥","Nanchang":"江西-南昌",
"Chengdu":"四川-成都","Fuzhou":"福建-福州","Xiamen":"福建-厦门","Haikou":"海南-海口",
"Nanning":"广西-南宁","Hechi":"广西-河池","Hohhot":"内蒙古-呼和浩特",
"Xi'an":"陕西-西安","Xian":"陕西-西安","Taiyuan":"山西-太原","Shenyang":"辽宁-沈阳",
"Dalian":"辽宁-大连","Changchun":"吉林-长春","Harbin":"黑龙江-哈尔滨",
"Kunming":"云南-昆明","Guiyang":"贵州-贵阳","Lanzhou":"甘肃-兰州","Xining":"青海-西宁",
"Yinchuan":"宁夏-银川","Urumqi":"新疆-乌鲁木齐","Lhasa":"西藏-拉萨"
}

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"china-ip-builder"})
    with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)

rows=[]
# ProxyScrape
try:
    for p in get(SOURCES[0]):
        if p.get("country_code")=="CN" and p.get("city") in CITY and p.get("anonymity")!="transparent":
            rows.append(dict(protocol=p["protocol"],ip=p["ip"],port=p["port"],city=p["city"],
                uptime=float(p.get("uptime_percent") or 0), latency=float(p.get("latency_ms") or 999999)))
except Exception as e: print("ProxyScrape:",e)

# monosans: verified hourly; geolocation metadata
try:
    for p in get(SOURCES[1]):
        geo=p.get("geolocation") or {}
        country=((geo.get("country") or {}).get("iso_code") or "").upper()
        city=(((geo.get("city") or {}).get("names") or {}).get("en"))
        proto=p.get("protocol")
        if country=="CN" and city in CITY and proto in ("http","socks4","socks5"):
            rows.append(dict(protocol=proto,ip=p.get("host"),port=p.get("port"),city=city,
                uptime=100, latency=float(p.get("timeout") or 999)*1000))
except Exception as e: print("monosans:",e)

# dedupe, then keep best 3 per province/city
seen=set(); rows2=[]
for p in sorted(rows,key=lambda x:(-x["uptime"],x["latency"])):
    k=(p["protocol"],p["ip"],p["port"])
    if k not in seen and p["ip"] and p["port"]:
        seen.add(k); rows2.append(p)

bucket={}
for p in rows2:
    loc=CITY[p["city"]]
    bucket.setdefault(loc,[])
    if len(bucket[loc])<3: bucket[loc].append(p)

selected=[p for loc in sorted(bucket) for p in bucket[loc]]
names=[]
lines=[
"# Auto-generated mainland China public proxy subscription for Shadowrocket / Clash",
"# Sources: ProxyScrape + monosans. Public proxies are untrusted and may disappear at any time.",
"proxies:"
]
for i,p in enumerate(selected,1):
    loc=CITY[p["city"]]
    name=f"🇨🇳 {loc} {p['protocol'].upper()} {i:02d}"
    names.append(name)
    lines.append(f'  - {{name: "{name}", type: {p["protocol"]}, server: {p["ip"]}, port: {p["port"]}}}')
lines += ['proxy-groups:','  - name: "🇨🇳 国内IP"','    type: select','    proxies:']
lines += [f'      - "{n}"' for n in names]
lines += ['rules:','  - MATCH,🇨🇳 国内IP','']
open("china-proxy.yaml","w",encoding="utf-8").write("\n".join(lines))
print("nodes",len(selected),"locations",len(bucket),sorted(bucket))
