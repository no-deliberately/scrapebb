# danmaku_extractor.py
import os
import json
import pandas as pd
import dm_pb2 as Danmaku
from tqdm import tqdm
from danmaku_parser import DanmakuParser

class DanmakuExtractor:
    def __init__(self, base_dir="./data"):
        """初始化弹幕提取器"""
        self.base_dir = base_dir
        self.danmaku_dir = os.path.join(base_dir, "弹幕数据")
        self.output_dir = os.path.join(base_dir, "处理后的弹幕")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def parse_single_danmaku_file(self, bin_file_path):
        """解析单个弹幕文件为DataFrame格式"""
        try:
            # 使用DanmakuParser解析二进制文件
            danmaku_seg = DanmakuParser.parse_danmaku_bin(bin_file_path)
            
            if not danmaku_seg:
                return None
            
            # 提取弹幕信息
            danmaku_list = []
            for elem in danmaku_seg.elems:
                danmaku_info = {
                    'progress': elem.progress / 1000.0,  # 转换为秒
                    'content': elem.content,
                    'mode': elem.mode,
                    'font_size': elem.fontsize,
                    'color': elem.color,
                    'timestamp': elem.ctime,
                    'weight': elem.weight,
                    'pool': elem.pool,
                    'mid_hash': elem.midHash
                }
                danmaku_list.append(danmaku_info)
            
            return pd.DataFrame(danmaku_list)
        except Exception as e:
            print(f"解析文件失败 {bin_file_path}: {str(e)}")
            return None
    
    def process_video_folder(self, video_folder):
        """处理单个视频文件夹的所有弹幕数据"""
        # 读取元数据
        metadata_path = os.path.join(video_folder, "metadata.json")
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 合并所有分段的弹幕数据
        all_segments_df = []
        for segment_file in sorted(os.listdir(video_folder)):
            if segment_file.startswith("segment_") and segment_file.endswith(".bin"):
                df = self.parse_single_danmaku_file(os.path.join(video_folder, segment_file))
                if df is not None:
                    # 添加视频信息
                    df['video_id'] = metadata['aid']
                    df['video_title'] = metadata['title']
                    df['cid'] = metadata['cid']
                    df['segment'] = int(segment_file.split('_')[1].split('.')[0])
                    all_segments_df.append(df)
        
        if all_segments_df:
            return pd.concat(all_segments_df, ignore_index=True)
        return None
    
    def process_all_videos(self):
        """处理所有视频的弹幕数据"""
        # 获取所有视频文件夹
        video_folders = [f for f in os.listdir(self.danmaku_dir) 
                        if os.path.isdir(os.path.join(self.danmaku_dir, f))]
        
        print(f"开始处理 {len(video_folders)} 个视频的弹幕数据...")
        
        # 创建一个空的DataFrame列表，用于存储所有视频的弹幕数据
        all_danmaku_dfs = []
        
        # 处理每个视频文件夹
        for folder in tqdm(video_folders, desc="处理视频文件夹"):
            video_path = os.path.join(self.danmaku_dir, folder)
            df = self.process_video_folder(video_path)
            
            if df is not None:
                all_danmaku_dfs.append(df)
        
        # 合并所有DataFrame
        if all_danmaku_dfs:
            print("合并所有弹幕数据...")
            final_df = pd.concat(all_danmaku_dfs, ignore_index=True)
            
            print(f"总计处理了 {len(video_folders)} 个视频，{len(final_df)} 条弹幕")
            
            # 保存一份CSV格式
            csv_file = os.path.join(self.output_dir, "all_danmaku.csv")
            final_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"已保存CSV格式数据到: {csv_file}")
            
            # 显示数据统计信息
            print("\n数据统计:")
            print(f"- 总视频数: {final_df['video_id'].nunique()}")
            print(f"- 总弹幕数: {len(final_df)}")
            print(f"- 每个视频平均弹幕数: {len(final_df) / final_df['video_id'].nunique():.2f}")
            
            return final_df
        else:
            print("没有找到任何有效的弹幕数据")
            return None


def main():
    # 设置基础目录，根据实际情况修改
    base_dir = "./data"
    
    extractor = DanmakuExtractor(base_dir)
    extractor.process_all_videos()


if __name__ == "__main__":
    main()