# coding=utf-8
#!/usr/bin/python
import json
import sys
import uuid
import copy
import re
sys.path.append('..')
from base.spider import Spider
from concurrent.futures import ThreadPoolExecutor, as_completed


class Spider(Spider):

    def init(self, extend=""):
        self.dbody = {
            "page_params": {
                "channel_id": "",
                "filter_params": "sort=75",
                "page_type": "channel_operation",
                "page_id": "channel_list_second_page"
            }
        }
        self.body = self.dbody

    def getName(self):
        return "首页"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    host = 'https://v.qq.com'
    apihost = 'https://pbaccess.video.qq.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5410.0 Safari/537.36',
        'origin': host,
        'referer': f'{host}/',
        'Content-Type': 'application/json'
    }

    def homeContent(self, filter):
        cdata = {
            "电视剧": "100113",
            "电影": "100173", 
            "综艺": "100109",
            "纪录片": "100105",
            "动漫": "100119",
            "少儿": "100150",
            "短剧": "110755"
        }
        result = {}
        classes = []
        filters = {}
        
        for k in cdata:
            classes.append({
                'type_name': k,
                'type_id': cdata[k]
            })
            
        with ThreadPoolExecutor(max_workers=len(classes)) as executor:
            futures = [executor.submit(self.get_filter_data, item['type_id']) for item in classes]
            for future in futures:
                try:
                    cid, data = future.result()
                    if not data.get('data', {}).get('module_list_datas'):
                        continue
                    filter_dict = {}
                    try:
                        items = data['data']['module_list_datas'][-1]['module_datas'][-1]['item_data_lists']['item_datas']
                        for item in items:
                            if not item.get('item_params', {}).get('index_item_key'):
                                continue
                            params = item['item_params']
                            filter_key = params['index_item_key']
                            if filter_key not in filter_dict:
                                filter_dict[filter_key] = {
                                    'key': filter_key,
                                    'name': params['index_name'],
                                    'value': []
                                }
                            filter_dict[filter_key]['value'].append({
                                'n': params['option_name'],
                                'v': params['option_value']
                            })
                    except:
                        continue
                    filters[cid] = list(filter_dict.values())
                except:
                    continue
                    
        result['class'] = classes
        if filters:
            result['filters'] = filters
        return result

    def homeVideoContent(self):
        try:
            json_data = {
                'page_context': None,
                'page_params': {
                    'page_id': '100101',
                    'page_type': 'channel',
                    'skip_privacy_types': '0',
                    'support_click_scan': '1',
                    'new_mark_label_enabled': '1',
                    'ams_cookies': ''
                },
                'page_bypass_params': {
                    'params': {
                        'caller_id': '',
                        'data_mode': 'default',
                        'page_id': '',
                        'page_type': 'channel',
                        'platform_id': '2',
                        'user_mode': 'default'
                    },
                    'scene': 'channel',
                    'abtest_bypass_id': ''
                }
            }
            data = self.post(f'{self.apihost}/trpc.vector_layout.page_view.PageService/getPage', 
                           headers=self.headers, json=json_data).json()
            vlist = []
            
            card_locations = [
                data.get('data', {}).get('CardList', [{}])[0].get('children_list', {}).get('list', {}).get('cards', []),
                data.get('data', {}).get('module_list_datas', []),
                data.get('data', {}).get('card_list', [])
            ]
            
            for cards in card_locations:
                if not cards:
                    continue
                    
                for it in cards:
                    try:
                        if it.get('params'):
                            p = it['params']
                            tag = json.loads(p.get('uni_imgtag', '{}') or p.get('imgtag', '{}') or '{}')
                            id = it.get('id') or p.get('cid') or p.get('video_id')
                            name = p.get('mz_title') or p.get('title') or p.get('name')
                            
                            if name and id and 'http' not in str(id):
                                vlist.append({
                                    'vod_id': id,
                                    'vod_name': name,
                                    'vod_pic': p.get('image_url') or p.get('pic_url') or p.get('cover_url'),
                                    'vod_year': tag.get('tag_2', {}).get('text', ''),
                                    'vod_remarks': tag.get('tag_4', {}).get('text', '') or tag.get('tag_3', {}).get('text', '')
                                })
                        elif it.get('item_params'):
                            p = it['item_params']
                            tag = json.loads(p.get('uni_imgtag', '{}') or p.get('imgtag', '{}') or '{}')
                            id = p.get('cid') or p.get('video_id')
                            name = p.get('mz_title') or p.get('title')
                            
                            if name and id:
                                vlist.append({
                                    'vod_id': id,
                                    'vod_name': name,
                                    'vod_pic': p.get('new_pic_hz') or p.get('new_pic_vt') or p.get('image_url'),
                                    'vod_year': tag.get('tag_2', {}).get('text', ''),
                                    'vod_remarks': tag.get('tag_4', {}).get('text', '')
                                })
                    except:
                        continue
                        
                if vlist:  
                    break
                    
            return {'list': vlist}
            
        except:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            result = {}
           
            params = {
                "sort": extend.get('sort', '75'),
                "attr": extend.get('attr', '-1'),
                "itype": extend.get('itype', '-1'),
                "ipay": extend.get('ipay', '-1'),
                "iarea": extend.get('iarea', '-1'),
                "iyear": extend.get('iyear', '-1'),
                "theater": extend.get('theater', '-1'),
                "award": extend.get('award', '-1'),
                "recommend": extend.get('recommend', '-1')
            }
            
            if pg == '1':
                self.body = copy.deepcopy(self.dbody)
                
            self.body['page_params']['channel_id'] = tid
            self.body['page_params']['filter_params'] = self.josn_to_params(params)
            
            data = self.post(
                f'{self.apihost}/trpc.universal_backend_service.page_server_rpc.PageServer/GetPageData?video_appid=1000005&vplatform=2&vversion_name=8.9.10&new_mark_label_enabled=1',
                json=self.body, headers=self.headers).json()
                
            ndata = data.get('data', {})
            if not ndata:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
                
            if ndata.get('has_next_page'):
                result['pagecount'] = 9999
                self.body['page_context'] = ndata.get('next_page_context', '')
            else:
                result['pagecount'] = int(pg)
                
            vlist = []
            module_datas = ndata.get('module_list_datas', [])
            if module_datas:
                for module in reversed(module_datas):
                    for sub_module in module.get('module_datas', []):
                        item_lists = sub_module.get('item_data_lists', {})
                        items = item_lists.get('item_datas', [])
                        for its in items:
                            try:
                                p = its.get('item_params', {})
                                if not p:
                                    continue
                                    
                                id = p.get('cid') or p.get('video_id')
                                if not id:
                                    continue
                                    
                                tag = json.loads(p.get('uni_imgtag', '{}') or p.get('imgtag', '{}') or '{}')
                                name = p.get('mz_title') or p.get('title')
                                pic = p.get('new_pic_hz') or p.get('new_pic_vt') or p.get('image_url')
                                
                                vlist.append({
                                    'vod_id': id,
                                    'vod_name': name,
                                    'vod_pic': pic,
                                    'vod_year': tag.get('tag_2', {}).get('text', ''),
                                    'vod_remarks': tag.get('tag_4', {}).get('text', '')
                                })
                            except:
                                continue
                                
                    if vlist:  
                        break
                        
            result['list'] = vlist
            result['page'] = pg
            result['limit'] = 90
            result['total'] = 999999
            return result
            
        except:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        try:
            vbody = {
                "page_params": {
                    "req_from": "web",
                    "cid": ids[0],
                    "vid": "",
                    "lid": "",
                    "page_type": "detail_operation", 
                    "page_id": "detail_page_introduction"
                },
                "has_cache": 1
            }
            body = {
                "page_params": {
                    "req_from": "web_vsite",
                    "page_id": "vsite_episode_list",
                    "page_type": "detail_operation",
                    "id_type": "1",
                    "page_size": "",
                    "cid": ids[0],
                    "vid": "",
                    "lid": "",
                    "page_num": "",
                    "page_context": "",
                    "detail_page_type": "1"
                },
                "has_cache": 1
            }
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_detail = executor.submit(self.get_vdata, vbody)
                future_episodes = executor.submit(self.get_vdata, body)
                vdata = future_detail.result()
                data = future_episodes.result()

            pdata = self.process_tabs(data, body, ids)
            if not pdata:
                return {'list': []}

            try:
                star_list = []
                try:
                    star_list = vdata['data']['module_list_datas'][0]['module_datas'][0]['item_data_lists']['item_datas'][0].get('sub_items', {}).get('star_list', {}).get('item_datas', [])
                except:
                    pass
                    
                actors = [star['item_params']['name'] for star in star_list if star.get('item_params', {}).get('name')]
                
                names = ['腾讯视频']
                plist, ylist = self.process_pdata(pdata, ids)
                
                all_episodes = plist + ylist
                
                if all_episodes:
                    urls = ['#'.join(all_episodes)]
                    vod = self.build_vod(vdata, actors, all_episodes, names)
                else:
                    default_play = f"正片${ids[0]}@default"
                    urls = [default_play]
                    vod = self.build_vod(vdata, actors, [default_play], names)
                
                return {'list': [vod]}
            except:
                return {'list': []}
                
        except:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            headers = self.headers.copy()
            headers.update({'Content-Type': 'application/json'})
            
            body = {
                "version": "25042201",
                "clientType": 1,
                "filterValue": "",
                "uuid": str(uuid.uuid4()).upper(),
                "retry": 0,
                "query": key,
                "pagenum": int(pg) - 1,
                "isPrefetch": True,
                "pagesize": 30,
                "queryFrom": 0,
                "searchDatakey": "",
                "transInfo": "",
                "isneedQc": True,
                "preQid": "",
                "adClientInfo": "",
                "extraInfo": {
                    "isNewMarkLabel": "1",
                    "multi_terminal_pc": "1",
                    "themeType": "1",
                    "sugRelatedIds": "{}",
                    "appVersion": ""
                }
            }
            
            data = self.post(f'{self.apihost}/trpc.videosearch.mobile_search.MultiTerminalSearch/MbSearch?vplatform=2',
                           json=body, headers=headers).json()
            vlist = []
            vname = ["电视剧", "电影", "综艺", "纪录片", "动漫", "少儿", "短剧"]
            
            normal_list = data.get('data', {}).get('normalList', {}).get('itemList', [])
            
            for k in normal_list:
                try:
                    if not (k.get('doc') and k.get('videoInfo')):
                        continue
                        
                    doc_id = k['doc'].get('id', '')
                    video_info = k['videoInfo']
                    sub_title = video_info.get('subTitle', '')
                    title = video_info.get('title', '')
                    type_name = video_info.get('typeName', '')
                    
                    if doc_id in ['MainNeed', 'ad']:
                        continue
                        
                    if (not doc_id or 
                        '外站' in sub_title or 
                        not title or 
                        type_name not in vname or
                        len(doc_id) <= 11):
                        continue
                    
                    search_key_lower = key.lower()
                    title_lower = title.lower()
                    
                    if search_key_lower not in title_lower:
                        continue
                        
                    img_tag = video_info.get('imgTag')
                    if img_tag and isinstance(img_tag, str):
                        try:
                            tag = json.loads(img_tag)
                        except:
                            tag = {}
                    else:
                        tag = {}
                        
                    pic = video_info.get('imgUrl', '')
                    
                    vlist.append({
                        'vod_id': doc_id,
                        'vod_name': self.removeHtmlTags(title),
                        'vod_pic': pic,
                        'vod_year': f"{type_name} {tag.get('tag_2', {}).get('text', '')}".strip(),
                        'vod_remarks': tag.get('tag_4', {}).get('text', '') or tag.get('tag_3', {}).get('text', '')
                    })
                except:
                    continue
                    
            if len(vlist) < 5:
                area_list = data.get('data', {}).get('areaBoxList', [{}])[0].get('itemList', []) if data.get('data', {}).get('areaBoxList') else []
                for k in area_list:
                    try:
                        if not (k.get('doc') and k.get('videoInfo')):
                            continue
                            
                        doc_id = k['doc'].get('id', '')
                        video_info = k['videoInfo']
                        sub_title = video_info.get('subTitle', '')
                        title = video_info.get('title', '')
                        type_name = video_info.get('typeName', '')
                        
                        if (not doc_id or 
                            '外站' in sub_title or 
                            not title or 
                            type_name not in vname or
                            len(doc_id) <= 11):
                            continue
                        
                        search_key_lower = key.lower()
                        title_lower = title.lower()
                        
                        if search_key_lower not in title_lower:
                            continue
                            
                        img_tag = video_info.get('imgTag')
                        if img_tag and isinstance(img_tag, str):
                            try:
                                tag = json.loads(img_tag)
                            except:
                                tag = {}
                        else:
                            tag = {}
                            
                        pic = video_info.get('imgUrl', '')
                        
                        vlist.append({
                            'vod_id': doc_id,
                            'vod_name': self.removeHtmlTags(title),
                            'vod_pic': pic,
                            'vod_year': f"{type_name} {tag.get('tag_2', {}).get('text', '')}".strip(),
                            'vod_remarks': tag.get('tag_4', {}).get('text', '') or tag.get('tag_3', {}).get('text', '')
                        })
                    except:
                        continue
                    
            return {'list': vlist, 'page': pg}
            
        except:
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        try:
            if '$' in id:
                play_id = id.split('$')[1]
                ids = play_id.split('@')
            else:
                ids = id.split('@')
            
            if len(ids) >= 2:
                cid = ids[0]
                vid = ids[1]
                url = f"{self.host}/x/cover/{cid}/{vid}.html"
                
                return {
                    'parse': 1,
                    'url': url,
                    'header': ''
                }
            else:
                url = f"{self.host}/x/cover/{id}.html"
                return {
                    'parse': 1,
                    'url': url,
                    'header': ''
                }
                
        except:
            url = f"{self.host}/x/cover/{id}.html"
            return {
                'parse': 1,
                'url': url,
                'header': ''
            }

    def localProxy(self, param):
        pass

    def get_filter_data(self, cid):
        try:
            hbody = copy.deepcopy(self.dbody)
            hbody['page_params']['channel_id'] = cid
            data = self.post(
                f'{self.apihost}/trpc.universal_backend_service.page_server_rpc.PageServer/GetPageData?video_appid=1000005&vplatform=2&vversion_name=8.9.10&new_mark_label_enabled=1',
                json=hbody, headers=self.headers).json()
            return cid, data
        except:
            return cid, {}

    def get_vdata(self, body):
        try:
            vdata = self.post(
                f'{self.apihost}/trpc.universal_backend_service.page_server_rpc.PageServer/GetPageData?video_appid=3000010&vplatform=2&vversion_name=8.2.96',
                json=body, headers=self.headers
            ).json()
            return vdata
        except:
            return {'data': {'module_list_datas': []}}

    def process_pdata(self, pdata, ids):
        plist = []
        ylist = []
        for k in pdata:
            if k.get('item_id'):
                item_params = k.get('item_params', {})
                title = item_params.get('union_title', '') or item_params.get('title', '')
                item_id = k['item_id']
                
                if title and item_id:
                    pid = f"{title}${ids[0]}@{item_id}"
                    title_lower = title.lower()
                    trailer_keywords = ['预告', '花絮', '特辑', '片段', '抢先看']
                    
                    if any(keyword in title_lower for keyword in trailer_keywords):
                        ylist.append(pid)
                    else:
                        plist.append(pid)
        return plist, ylist

    def build_vod(self, vdata, actors, episodes, names):
        try:
            main_data = vdata['data']['module_list_datas'][0]['module_datas'][0]['item_data_lists']['item_datas'][0]
            d = main_data.get('item_params', {})
            
            urls = []
            if episodes:
                urls.append('#'.join(episodes))
                
            vod = {
                'vod_id': d.get('cid', ''),
                'type_name': d.get('sub_genre', ''),
                'vod_name': d.get('title', ''),
                'vod_year': d.get('year', ''),
                'vod_area': d.get('area_name', ''),
                'vod_remarks': d.get('holly_online_time', '') or d.get('hotval', ''),
                'vod_actor': ','.join(actors),
                'vod_director': d.get('director', ''),
                'vod_content': d.get('cover_description', '') or d.get('description', ''),
                'vod_play_from': '$$$'.join(names) if names else '腾讯视频',
                'vod_play_url': '$$$'.join(urls) if urls else ''
            }
            return {k: v for k, v in vod.items() if v}  
        except:
            return {}

    def process_tabs(self, data, body, ids):
        try:
            pdata = data['data']['module_list_datas'][-1]['module_datas'][-1]['item_data_lists']['item_datas']
            tabs = data['data']['module_list_datas'][-1]['module_datas'][-1]['module_params'].get('tabs')
            
            if tabs and len(json.loads(tabs)) > 1:
                tabs = json.loads(tabs)
                remaining_tabs = tabs[1:]
                task_queue = []
                
                for tab in remaining_tabs:
                    nbody = copy.deepcopy(body)
                    nbody['page_params']['page_context'] = tab['page_context']
                    task_queue.append(nbody)
                    
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_map = {executor.submit(self.get_vdata, task): idx for idx, task in enumerate(task_queue)}
                    results = [None] * len(task_queue)
                    
                    for future in as_completed(future_map):
                        idx = future_map[future]
                        try:
                            results[idx] = future.result()
                        except:
                            pass
                            
                    for result in results:
                        if result and result.get('data'):
                            module_datas = result['data'].get('module_list_datas', [])
                            if module_datas:
                                page_data = module_datas[-1]['module_datas'][-1]['item_data_lists']['item_datas']
                                pdata.extend(page_data)
            return pdata
        except:
            try:
                return data['data']['module_list_datas'][-1]['module_datas'][-1]['item_data_lists']['item_datas']
            except:
                return []

    def josn_to_params(self, params, skip_empty=True):
        query = []
        for k, v in params.items():
            if skip_empty and (v is None or v == '' or v == '-1'):
                continue
            query.append(f"{k}={v}")
        return "&".join(query)

    def removeHtmlTags(self, text):
        if not text:
            return ''
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)