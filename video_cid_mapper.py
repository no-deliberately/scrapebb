# video_cid_mapper.py
import os
import json
import time
import random
import requests
import re
from typing import Dict, Optional, List, Any

class VideoCIDMapper:
    def __init__(self, base_dir: str):
        """初始化CID映射器"""
        self.base_dir = base_dir
        self.output_file = os.path.join(base_dir, "视频CID映射.json")
    
    def extract_video_id(self, arcurl: str) -> Optional[Dict[str, Any]]:
        """从arcurl中提取AV号或BV号"""
        av_match = re.search(r'av(\d+)', arcurl, re.IGNORECASE)
        if av_match:
            return {'aid': int(av_match.group(1))}
        
        bv_match = re.search(r'(BV\w+)', arcurl, re.IGNORECASE)
        if bv_match:
            return {'bvid': bv_match.group(1)}
        
        return None
    
    def get_video_cid(self, video_id_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用AV号或BV号获取CID"""
        url = "https://api.bilibili.com/x/web-interface/view"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, params=video_id_dict, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result['code'] == 0:
                main_cid = result['data']['cid']
                all_parts = [
                    {'part_number': page['page'], 'part_name': page['part'], 'cid': page['cid']}
                    for page in result['data'].get('pages', [])
                ]
                return {
                    'main_cid': main_cid, 
                    'title': result['data'].get('title', ''), 
                    'parts': all_parts if all_parts else None
                }
            else:
                print(f"API错误: {result['code']} - {result['message']}")
        except requests.RequestException as e:
            print(f"请求错误: {e}")
        except Exception as e:
            print(f"获取CID时发生异常: {e}")
        
        return None
    
    def random_sleep(self) -> float:
        """随机休眠一段时间，避免请求过于频繁"""
        sleep_time = random.uniform(0.5, 2.0)
        time.sleep(sleep_time)
        return sleep_time
    
    def process_search_results(self) -> None:
        """处理所有搜索结果文件，创建arcurl和CID之间的映射"""
        # 如果映射文件已存在，加载已处理的视频映射
        video_cid_map = {}
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                video_cid_map = json.load(f)
        
        # 进度跟踪计数器
        total_files, processed_files, total_videos, processed_videos, failed_videos = 0, 0, 0, 0, 0
        
        # 计算需要处理的文件总数
        for keyword_dir in os.listdir(self.base_dir):
            keyword_path = os.path.join(self.base_dir, keyword_dir)
            if os.path.isdir(keyword_path):
                for category_dir in os.listdir(keyword_path):
                    category_path = os.path.join(keyword_path, category_dir)
                    if os.path.isdir(category_path):
                        total_files += len([f for f in os.listdir(category_path) if f.endswith('.json')])
        
        print(f"找到 {total_files} 个JSON文件需要处理")
        
        # 处理文件
        for keyword_dir in os.listdir(self.base_dir):
            keyword_path = os.path.join(self.base_dir, keyword_dir)
            if os.path.isdir(keyword_path):
                print(f"\n正在处理关键词目录: {keyword_dir}")
                for category_dir in os.listdir(keyword_path):
                    category_path = os.path.join(keyword_path, category_dir)
                    if os.path.isdir(category_path):
                        print(f"  正在处理分类: {category_dir}")
                        for filename in os.listdir(category_path):
                            if filename.endswith('.json'):
                                self._process_file(
                                    category_path, filename, video_cid_map,
                                    processed_files, total_files, total_videos,
                                    processed_videos, failed_videos
                                )
        
        # 保存最终映射
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(video_cid_map, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理完成!")
        print(f"找到的视频总数: {total_videos}")
        print(f"成功处理: {processed_videos}")
        print(f"处理失败: {failed_videos}")
        print(f"映射已保存至: {self.output_file}")
    
    def _process_file(
        self, category_path: str, filename: str, video_cid_map: Dict[str, Any],
        processed_files: int, total_files: int, total_videos: int,
        processed_videos: int, failed_videos: int
    ) -> tuple:
        """处理单个JSON文件"""
        file_path = os.path.join(category_path, filename)
        processed_files += 1
        print(f"    正在处理文件 {processed_files}/{total_files}: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                search_data = json.load(f)
            
            if 'data' in search_data and 'result' in search_data['data']:
                video_results = search_data['data']['result']
                
                for video in video_results:
                    arcurl = video.get('arcurl')
                    # 检查arcurl是否已经在映射中
                    if not arcurl or arcurl in video_cid_map:
                        continue
                    
                    total_videos += 1
                    video_id_dict = self.extract_video_id(arcurl)
                    
                    if video_id_dict:
                        sleep_time = self.random_sleep()
                        cid_info = self.get_video_cid(video_id_dict)
                        
                        if cid_info:
                            video_cid_map[arcurl] = {
                                'aid': video.get('aid'),
                                'bvid': video.get('bvid'),
                                'title': video.get('title'),
                                'cid_info': cid_info
                            }
                            
                            processed_videos += 1
                            print(f"      ({processed_videos}/{total_videos}) 已处理: {arcurl} -> CID: {cid_info['main_cid']} (等待 {sleep_time:.2f}秒)")
                            
                            if processed_videos % 50 == 0:
                                with open(self.output_file, 'w', encoding='utf-8') as f:
                                    json.dump(video_cid_map, f, ensure_ascii=False, indent=2)
                                print(f"      已保存进度: 已处理 {processed_videos} 个视频")
                        else:
                            failed_videos += 1
                            print(f"      获取CID失败: {arcurl}")
                    else:
                        failed_videos += 1
                        print(f"      无效的arcurl格式: {arcurl}")
        except Exception as e:
            print(f"    处理文件 {file_path} 时出错: {e}")
        
        return processed_files, total_videos, processed_videos, failed_videos


if __name__ == "__main__":
    # 基础目录（存放搜索结果的地方）
    base_dir = "./data/search_results"
    
    mapper = VideoCIDMapper(base_dir)
    print("开始处理搜索结果以提取视频CID...")
    mapper.process_search_results()