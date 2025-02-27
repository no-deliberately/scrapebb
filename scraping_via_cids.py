import os
import json
import time
import random
import requests
import datetime
import base64
from tqdm import tqdm

# 基本配置
base_dir = r""
danmaku_dir = os.path.join(base_dir, "弹幕数据")
cid_mapping_file = os.path.join(base_dir, "视频CID映射.json")

# 确保弹幕保存目录存在
if not os.path.exists(danmaku_dir):
    os.makedirs(danmaku_dir)

def random_sleep(min_time=0.5, max_time=2.0):
    """随机休眠以避免请求过于频繁"""
    sleep_time = random.uniform(min_time, max_time)
    time.sleep(sleep_time)
    return sleep_time

def get_segment_danmaku(cid, segment_index=1, aid=None):
    """获取指定CID和分段的弹幕数据"""
    url = 'https://api.bilibili.com/x/v2/dm/web/seg.so'
    params = {
        'type': 1,
        'oid': cid,
        'segment_index': segment_index
    }
    
    if aid:
        params['pid'] = aid
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/video/"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"  HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"  获取弹幕时发生异常: {str(e)}")
        return None

def save_raw_danmaku(video_info, max_segments=10):
    """保存指定视频的所有分段弹幕数据"""
    cid = video_info.get('cid_info', {}).get('main_cid')
    title = video_info.get('title', '')
    aid = video_info.get('aid')
    bvid = video_info.get('bvid')
    
    if not cid:
        print(f"视频信息缺少CID: {title}")
        return None
    
    # 安全处理视频标题，用于文件名
    safe_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in title])
    safe_title = safe_title[:50]  # 限制长度
    
    # 创建视频专属目录
    video_dir = os.path.join(danmaku_dir, f"{aid}_{safe_title}")
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
    
    print(f"\n处理视频: {title} (CID: {cid})")
    
    # 收集元数据
    metadata = {
        'title': title,
        'aid': aid,
        'bvid': bvid,
        'cid': cid,
        'fetch_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'segments': {}
    }
    
    # 获取所有分段弹幕
    successfully_fetched = 0
    
    for segment_index in range(1, max_segments + 1):
        segment_data = get_segment_danmaku(cid, segment_index, aid)
        
        if segment_data and len(segment_data) > 10:  # 确保响应内容有效
            # 保存到二进制文件
            segment_file = os.path.join(video_dir, f"segment_{segment_index}.bin")
            with open(segment_file, 'wb') as f:
                f.write(segment_data)
            
            # 记录元数据
            segment_start_time = (segment_index - 1) * 6  # 每段6分钟
            metadata['segments'][segment_index] = {
                'file': segment_file,
                'size': len(segment_data),
                'start_time': f"{segment_start_time}:00",
                'end_time': f"{segment_start_time + 6}:00"
            }
            
            successfully_fetched += 1
            print(f"  成功获取第 {segment_index} 段弹幕 ({len(segment_data)} 字节)")
        else:
            print(f"  第 {segment_index} 段弹幕无效或视频不足这么长")
            break
        
        random_sleep()
    
    # 保存元数据到JSON
    metadata_file = os.path.join(video_dir, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"成功获取 {successfully_fetched} 个分段弹幕，元数据已保存至 {metadata_file}")
    return metadata

def process_cid_mapping():
    """处理CID映射文件中的所有视频"""
    if not os.path.exists(cid_mapping_file):
        print(f"错误: CID映射文件不存在: {cid_mapping_file}")
        return
    
    # 加载CID映射
    with open(cid_mapping_file, 'r', encoding='utf-8') as f:
        video_mapping = json.load(f)
    
    print(f"加载了 {len(video_mapping)} 个视频的CID映射")
    
    # 选择处理模式
    print("\n请选择处理方式:")
    print("1. 处理所有视频")
    print("2. 处理指定数量的视频")
    print("3. 根据关键词过滤视频")
    print("4. 处理指定分类的视频")
    
    mode = input("请输入选择 (1/2/3/4): ")
    
    videos_to_process = []
    
    if mode == '1':
        videos_to_process = list(video_mapping.values())
    elif mode == '2':
        try:
            count = int(input("请输入要处理的视频数量: "))
            videos_to_process = list(video_mapping.values())[:count]
        except ValueError:
            print("输入无效，请输入数字")
            return
    elif mode == '3':
        keyword = input("请输入筛选关键词: ")
        videos_to_process = [v for v in video_mapping.values() 
                         if keyword.lower() in v.get('title', '').lower()]
        print(f"找到 {len(videos_to_process)} 个匹配的视频")
    elif mode == '4':
        # 提取所有的视频URL，并从中获取关键词分类信息
        categories = set()
        for url, info in video_mapping.items():
            parts = url.split('/')
            for i, part in enumerate(parts):
                if "keyword" in part and i+1 < len(parts):
                    categories.add(parts[i+1])
        
        print("\n可用的分类:")
        for i, category in enumerate(sorted(categories)):
            print(f"{i+1}. {category}")
        
        try:
            category_index = int(input("\n请输入分类序号: ")) - 1
            selected_category = sorted(categories)[category_index]
            
            videos_to_process = [v for url, v in video_mapping.items() 
                             if selected_category in url]
            print(f"找到 {len(videos_to_process)} 个属于分类 '{selected_category}' 的视频")
        except (ValueError, IndexError):
            print("输入无效")
            return
    else:
        print("选择无效")
        return
    
    # 处理选定的视频
    total_videos = len(videos_to_process)
    processed = 0
    success = 0
    
    for video_info in tqdm(videos_to_process, desc="处理视频"):
        processed += 1
        try:
            result = save_raw_danmaku(video_info)
            if result:
                success += 1
            
            # 每10个视频报告一次进度
            if processed % 10 == 0 or processed == total_videos:
                print(f"\n进度: {processed}/{total_videos} 视频 ({success} 成功)")
        except Exception as e:
            print(f"处理视频时发生异常: {str(e)}")
        
        # 视频之间适当休眠，避免请求过于频繁
        if processed < total_videos:
            random_sleep(1.0, 3.0)
    
    print(f"\n处理完成! 总计 {processed} 个视频，{success} 个成功")

def main():
    print("B站视频弹幕爬取工具")
    print("=" * 40)
    print("本工具将从CID映射文件中读取视频信息，并获取每个视频的实时弹幕分包")
    
    # 确认CID映射文件存在
    if not os.path.exists(cid_mapping_file):
        print(f"错误: CID映射文件不存在: {cid_mapping_file}")
        return
    
    process_cid_mapping()

if __name__ == "__main__":
    # 安装必要的库
    # pip install requests tqdm
    main()