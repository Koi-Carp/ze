import json
import re
import sys
from base64 import b64decode, b64encode
from urllib.parse import urlparse, parse_qs, unquote, quote
import requests
from Crypto.Cipher import AES
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider as BaseSpider

img_cache = {}

class Spider(BaseSpider):
    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        self.host = self.get_working_host()
        self.headers.update({'Origin': self.host, 'Referer': f"{self.host}/"})

    def getName(self):
        return "💋 91短视频"

    def isVideoFormat(self, url):
        return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

    def manualVideoCheck(self):
        return False

    def destroy(self):
        global img_cache
        img_cache.clear()

    def get_working_host(self):
        # 使用代码二中的固定host
        return 'https://down.nigx.cn/91-short.com'

    def getvs(self, data):
        """从代码二复制的视频列表解析方法"""
        videos = []
        for i in data.items():
            a = i("a")
            videos.append({
                'vod_id': a.attr('href'),
                'vod_name': a.attr('title'),
                'vod_pic': self.getProxyUrl() + "&url=" + i("img").attr("data-cover"),
                'vod_remark': i(".module-item-caption").text() or i(".module-item-ru").text(),
            })
        return videos

    def getProxyUrl(self):
        """从代码二复制的代理URL生成方法"""
        return "/local_proxy?type=image"

    def homeContent(self, filter):
        # 固定分类列表
        classes = [
            {'type_name': '推荐', 'type_id': '/short/recommend_home_list'},
            {'type_name': '最新', 'type_id': '/'},
            {'type_name': '美女正妹', 'type_id': '/short/label_related_list/Ug_pu_kskqY%3D'},
            {'type_name': '91大神', 'type_id': '/short/label_related_list/otDa4t6lDDQ%3D'},
            {'type_name': '国产高清', 'type_id': '/short/home_category_list/hd'},
            {'type_name': '排行', 'type_id': '/short/ranking_list'},
            {'type_name': '国产AV', 'type_id': '/short/label_related_list/1Bd0Zzp8D_E%3D'},
            {'type_name': '门事件', 'type_id': '/short/label_related_list/3QW8lOdBcls%3D'},
            {'type_name': '大象传媒', 'type_id': '/short/label_related_list/F16wCJ3LmWY%3D'},
            {'type_name': '情趣综艺', 'type_id': '/short/label_related_list/-0S1LwkskU4%3D'}
        ]

        try:
            resp = self.fetch(f"{self.host}/film/home_recommend_list", headers=self.headers)
            tab2 = pq(resp.content)("#tablist > a")
            for k in tab2.items():
                href = k.attr('href')
                if not href or "http" in href:
                    continue
                classes.append({
                    'type_name': k.text(),
                    'type_id': href,
                })
            
            # 获取首页视频列表
            res = requests.get(self.host, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'class': classes, 'list': self.getlist(self.getpq(res.text)('.module-item, .video-item'))}
        except Exception as e:
            print(f"homeContent error: {e}")
            return {'class': classes, 'list': []}

    def getlist(self, data):
        """代码一的getlist方法，但使用代码二的图片代理方式"""
        videos = []
        for item in data.items():
            a = item("a")
            img = item("img")
            title = a.attr('title') or img.attr('alt') or ''
            remark = item(".video-card-info-duration").text() or item(".video-time").text() or ''
            
            # 使用代码二的图片代理方式
            pic = self.getProxyUrl() + "&url=" + img.attr("src") if img.attr("src") else ""
            if not pic and img.attr("data-cover"):
                pic = self.getProxyUrl() + "&url=" + img.attr("data-cover")
            
            videos.append({
                'vod_id': a.attr('href'),
                'vod_name': title,
                'vod_pic': pic,
                'vod_remark': remark
            })
        return videos

    def getpq(self, html):
        """辅助方法：创建PyQuery对象"""
        return pq(html)

    def homeVideoContent(self):
        try:
            res = requests.get(self.host, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'list': self.getlist(self.getpq(res.text)('.module-item, .video-item'))}
        except:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            pg = int(pg) if pg else 1
            
            # 使用代码二的分页逻辑
            if pg == 1:
                resp = self.fetch(self.host + tid, headers=self.headers)
                qu = ".module-items > .module-item > .module-item-cover"
                doc = pq(resp.content)
                stext = doc('main').next('script').html()
                if tid not in img_cache:
                    img_cache[tid] = {}
                if stext:
                    img_cache[tid]['next_page'] = stext.strip().split('\n', 1)[0].strip().split('=', 1)[-1].replace('"', '').strip()
            else:
                if tid in img_cache and 'next_page' in img_cache[tid]:
                    resp = self.fetch(self.host + img_cache[tid]['next_page'], headers=self.headers)
                    qu = ".module-item > .module-item-cover"
                    doc = pq(resp.content.decode())
                    # 更新下一页信息
                    img_cache[tid]['next_page'] = doc("script").eq(-1).text()
                else:
                    return {'list': [], 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 0}
            
            result = {
                'list': self.getvs(doc(qu)),
                'page': pg,
                'pagecount': 9999,
                'limit': 90,
                'total': 999999
            }
            return result
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {'list': [], 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        try:
            u = ids[0] if ids[0].startswith('http') else f"{self.host}{ids[0]}"
            res = requests.get(u, headers=self.headers, proxies=self.proxies, timeout=15)
            html = res.text
            data = self.getpq(html)
            purl = ''

            # 尝试从iframe获取视频地址
            ifr = data('iframe').attr('src')
            if ifr:
                if not ifr.startswith('http'): 
                    ifr = f"{self.host}{ifr}"
                try:
                    qs = parse_qs(urlparse(ifr).query)
                    if 'url' in qs:
                        ex = qs['url'][0]
                        if '.m3u8' in ex or '.mp4' in ex: 
                            purl = ex
                except: 
                    pass

            # 使用代码二的解析方式
            if not purl:
                stext = data('.player-wrapper > script').eq(-1).html()
                if stext:
                    stext = stext.strip()
                    try:
                        url = stext.split('\n')[-1].split('=')[-1].replace('"', '').strip()
                        p = 0
                    except Exception as e:
                        url = u
                        p = 1
                    purl = f"{url}@@{p}"

            if not purl:
                # 回退到原来的正则匹配方式
                m = re.search(r'[?&]url=([^&"\']+\.m3u8[^&"\']*)', html)
                if m: 
                    purl = unquote(m.group(1))
                else:
                    m = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
                    if m: 
                        purl = m.group(1)
                    else:
                        purl = f"解析失败${u}"

            v = {
                'vod_director': '沐辰',
                'vod_play_from': '91——short',
                'vod_play_url': f'{data(".module-item-in").text() or data("h2.module-title").text()}${purl}',
                'vod_content': ''
            }

            # 添加标签信息
            try:
                tags, seen = [], set()
                links = data('.video-info-aux a, .tag-link, .module-info-tag a, .tags a')
                for tag in links.items():
                    text = tag.text().strip()
                    if text and text not in seen:
                        tags.append(text)
                        seen.add(text)
                if tags:
                    v['vod_actor'] = ' '.join(tags)
            except:
                pass

            return {'list': [v]}
        except Exception as e:
            print(f"detailContent error: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            # 使用代码二的搜索方式
            resp = self.fetch(f'{self.host}/search', headers=self.headers, params={'wd': key})
            qu = ".module-items > .module-item > .module-item-cover"
            data = pq(resp.content)(qu)
            return {'list': self.getvs(data), 'page': pg}
        except Exception as e:
            print(f"searchContent error: {e}")
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        if '@@' in id:
            url, p = id.split('@@')
            return {'parse': int(p), 'url': url}
        else:
            return {'parse': 0, 'url': id}

    def localProxy(self, param):
        """从代码二复制的图片代理方法"""
        res = self.fetch(param['url'])
        key = b'Jui7X#cdleN^3eZb'
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted = cipher.decrypt(res.content)
        return [200, res.headers.get('Content-Type'), decrypted]