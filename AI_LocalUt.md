# Shadowrocket: 2026-10-10 11:38:07
[General]
bypass-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32, ff02::fb/128
dns-server = system
fallback-dns-server = system
ipv6 = false
prefer-ipv6 = false
dns-direct-system = false
icmp-auto-reply = true
always-reject-url-rewrite = false
private-ip-answer = true
dns-direct-fallback-proxy = true
udp-policy-not-supported-behaviour = REJECT
use-local-host-item-for-proxy = false

[Rule]
# ============ СЛУЖЕБНЫЕ МАРШРУТЫ — ПЕРВЫМИ ============

# VPS с VLESS Reality — напрямую, чтобы исключить петлю маршрутизации
IP-CIDR,130.17.19.53/32,DIRECT,no-resolve

# Локальная сеть
IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
IP-CIDR,127.0.0.0/8,DIRECT,no-resolve

# ============ ЧЕРЕЗ VLESS REALITY ============

# Claude / Anthropic
DOMAIN-SUFFIX,claude.ai,PROXY
DOMAIN-SUFFIX,claude.com,PROXY
DOMAIN-SUFFIX,anthropic.com,PROXY
DOMAIN-SUFFIX,claudeusercontent.com,PROXY
DOMAIN-KEYWORD,anthropic,PROXY

# OpenAI: ChatGPT, Codex, API, Sora
DOMAIN-SUFFIX,openai.com,PROXY
DOMAIN-SUFFIX,chatgpt.com,PROXY
DOMAIN-SUFFIX,oaistatic.com,PROXY
DOMAIN-SUFFIX,oaiusercontent.com,PROXY
DOMAIN-SUFFIX,sora.com,PROXY
DOMAIN-SUFFIX,openaiapi-site.azureedge.net,PROXY
DOMAIN-SUFFIX,openaicom.imgix.net,PROXY
DOMAIN-SUFFIX,workos.com,PROXY
DOMAIN-KEYWORD,openaicom-api,PROXY

# Авторизация, капча, функции и телеметрия OpenAI/Claude
DOMAIN-SUFFIX,auth0.com,PROXY
DOMAIN-SUFFIX,arkoselabs.com,PROXY
DOMAIN-SUFFIX,challenges.cloudflare.com,PROXY
DOMAIN-SUFFIX,statsig.com,PROXY
DOMAIN-SUFFIX,statsigapi.net,PROXY
DOMAIN-SUFFIX,featuregates.org,PROXY
DOMAIN-SUFFIX,launchdarkly.com,PROXY
DOMAIN-SUFFIX,intercom.io,PROXY
DOMAIN-SUFFIX,intercomcdn.com,PROXY
DOMAIN-SUFFIX,livekit.cloud,PROXY
DOMAIN-SUFFIX,segment.io,PROXY
DOMAIN-SUFFIX,sentry.io,PROXY

# Google AI — выше общего правила google.com → DIRECT
DOMAIN,gemini.google.com,PROXY
DOMAIN,aistudio.google.com,PROXY
DOMAIN,makersuite.google.com,PROXY
DOMAIN,notebooklm.google.com,PROXY
DOMAIN,alkalimakersuite-pa.clients6.google.com,PROXY
DOMAIN,proactivebackend-pa.googleapis.com,PROXY
DOMAIN,ai.google.dev,PROXY
DOMAIN-SUFFIX,gemini.google,PROXY
DOMAIN-SUFFIX,generativelanguage.googleapis.com,PROXY
DOMAIN-SUFFIX,aiplatform.googleapis.com,PROXY
DOMAIN-SUFFIX,deepmind.com,PROXY

# Microsoft Copilot / GitHub Copilot
DOMAIN,copilot.microsoft.com,PROXY
DOMAIN,copilot.bing.com,PROXY
DOMAIN,sydney.bing.com,PROXY
DOMAIN,edgeservices.bing.com,PROXY
DOMAIN,copilot-proxy.githubusercontent.com,PROXY
DOMAIN-SUFFIX,githubcopilot.com,PROXY

# iCloud Private Relay
DOMAIN-SUFFIX,apple-relay.apple.com,PROXY
DOMAIN-SUFFIX,apple-relay.akamaized.net,PROXY
DOMAIN-SUFFIX,apple-relay.cloudflare.com,PROXY
DOMAIN-SUFFIX,apple-relay.fastly-edge.com,PROXY
DOMAIN-SUFFIX,apple-relay.mask.apple-dns.net,PROXY

# YouTube
#DOMAIN-SUFFIX,youtube.com,PROXY
#DOMAIN-SUFFIX,youtu.be,PROXY
#DOMAIN-SUFFIX,yt.be,PROXY
#DOMAIN-SUFFIX,ytimg.com,PROXY
#DOMAIN-SUFFIX,youtube-nocookie.com,PROXY
#DOMAIN-SUFFIX,googlevideo.com,PROXY
#DOMAIN-SUFFIX,ggpht.com,PROXY
#DOMAIN-SUFFIX,gvt1.com,PROXY
#DOMAIN-SUFFIX,gvt2.com,PROXY
#DOMAIN,youtubei.googleapis.com,PROXY
#DOMAIN,youtube.googleapis.com,PROXY
#DOMAIN-KEYWORD,youtube,PROXY

# Telegram
DOMAIN-SUFFIX,telegram.org,PROXY
DOMAIN-SUFFIX,telegram.me,PROXY
DOMAIN-SUFFIX,t.me,PROXY
DOMAIN-SUFFIX,telegra.ph,PROXY
DOMAIN-SUFFIX,telesco.pe,PROXY
DOMAIN-SUFFIX,tdesktop.com,PROXY
IP-CIDR,91.108.4.0/22,PROXY,no-resolve
IP-CIDR,91.108.8.0/22,PROXY,no-resolve
IP-CIDR,91.108.12.0/22,PROXY,no-resolve
IP-CIDR,91.108.16.0/22,PROXY,no-resolve
IP-CIDR,91.108.56.0/22,PROXY,no-resolve
IP-CIDR,109.239.140.0/24,PROXY,no-resolve
IP-CIDR,149.154.160.0/20,PROXY,no-resolve
IP-CIDR6,2001:B28:F23D::/48,PROXY,no-resolve
IP-CIDR6,2001:B28:F23F::/48,PROXY,no-resolve
IP-CIDR6,2001:67C:4E8::/48,PROXY,no-resolve

# Социальные сети и мессенджеры
DOMAIN-SUFFIX,instagram.com,PROXY
DOMAIN-SUFFIX,cdninstagram.com,PROXY
DOMAIN-SUFFIX,instagr.am,PROXY
DOMAIN-SUFFIX,facebook.com,PROXY
DOMAIN-SUFFIX,fbcdn.net,PROXY
DOMAIN-SUFFIX,fb.com,PROXY
DOMAIN-SUFFIX,fb.me,PROXY
DOMAIN-SUFFIX,meta.com,PROXY
DOMAIN-SUFFIX,twitter.com,PROXY
DOMAIN-SUFFIX,x.com,PROXY
DOMAIN-SUFFIX,t.co,PROXY
DOMAIN-SUFFIX,twimg.com,PROXY
DOMAIN-SUFFIX,discord.com,PROXY
DOMAIN-SUFFIX,discordapp.com,PROXY
DOMAIN-SUFFIX,discordapp.net,PROXY
DOMAIN-SUFFIX,discord.gg,PROXY
DOMAIN-SUFFIX,discord.media,PROXY
DOMAIN-SUFFIX,discordcdn.com,PROXY

# Прочие сервисы
DOMAIN-SUFFIX,figma.com,PROXY
DOMAIN-SUFFIX,figmausercontent.com,PROXY
DOMAIN-SUFFIX,patreon.com,PROXY
DOMAIN-SUFFIX,patreonusercontent.com,PROXY
DOMAIN-SUFFIX,medium.com,PROXY
DOMAIN-SUFFIX,mediumusercontent.com,PROXY
DOMAIN-SUFFIX,linkedin.com,PROXY
DOMAIN-SUFFIX,licdn.com,PROXY
DOMAIN-SUFFIX,soundcloud.com,PROXY
DOMAIN-SUFFIX,sndcdn.com,PROXY
DOMAIN-SUFFIX,spotify.com,PROXY
DOMAIN-SUFFIX,spotifycdn.com,PROXY
DOMAIN-SUFFIX,scdn.co,PROXY
DOMAIN-SUFFIX,netflix.com,PROXY
DOMAIN-SUFFIX,netflix.net,PROXY
DOMAIN-SUFFIX,nflxvideo.net,PROXY
DOMAIN-SUFFIX,nflximg.net,PROXY
DOMAIN-SUFFIX,nflximg.com,PROXY
DOMAIN-SUFFIX,nflxext.com,PROXY
DOMAIN-SUFFIX,nflxso.net,PROXY
DOMAIN-SUFFIX,twitch.tv,PROXY
DOMAIN-SUFFIX,twitchcdn.net,PROXY
DOMAIN-SUFFIX,jtvnw.net,PROXY
DOMAIN-SUFFIX,ttvnw.net,PROXY
DOMAIN-SUFFIX,vimeo.com,PROXY
DOMAIN-SUFFIX,vimeocdn.com,PROXY
DOMAIN-SUFFIX,coursera.org,PROXY
DOMAIN-SUFFIX,udemy.com,PROXY

# Проверка внешнего IP и DNS
DOMAIN-SUFFIX,browserleaks.com,PROXY
DOMAIN-SUFFIX,ipleak.net,PROXY
DOMAIN-SUFFIX,whoer.net,PROXY
DOMAIN-SUFFIX,dnsleaktest.com,PROXY

# ============ НАПРЯМУЮ ============

# Portal Pochtavip.com
DOMAIN-SUFFIX,pochtavip.com,DIRECT

# Yandex
DOMAIN-KEYWORD,yandex,DIRECT
DOMAIN-SUFFIX,yastatic.net,DIRECT
DOMAIN-SUFFIX,ya.ru,DIRECT

# Google Search и Gmail — специальные Google AI правила выше имеют приоритет
DOMAIN-SUFFIX,googlemail.com,DIRECT
DOMAIN-SUFFIX,gmail.com,DIRECT
DOMAIN-SUFFIX,google.com,DIRECT

# Российские домены и IP
DOMAIN-SUFFIX,xn--p1ai,DIRECT
DOMAIN-SUFFIX,ru,DIRECT
GEOIP,RU,DIRECT

# Всё остальное — через VLESS Reality
FINAL,DIRECT

[Host]
localhost = 127.0.0.1

