# video_info_processor.py
import os
import json
import pandas as pd
from tqdm import tqdm
from typing import Dict, List, Any

class VideoDataProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.search_results_dir = os.path.join(base_dir, "search_results")
        self.categories = ['生活', '知识', '美食']
    
    def get_folder_names(self) -> List[str]:
        """获取所有关键词文件夹名称"""
        return [d for d in os.listdir(self.search_results_dir) 
                if os.path.isdir(os.path.join(self.search_results_dir, d))]
    
    def extract_video_features(self, video_data: Dict[str, Any], keyword: str, category: str) -> Dict[str, Any]:
        """从单个视频数据中提取关键特征"""
        return {
            'video_id': video_data.get('aid', ''),
            'bvid': video_data.get('bvid', ''),
            'title': video_data.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
            'author': video_data.get('author', ''),
            'mid': video_data.get('mid', 0),  # UP主ID
            'play_count': video_data.get('play', 0),
            'danmaku_count': video_data.get('video_review', 0),
            'comment_count': video_data.get('review', 0),
            'favorite_count': video_data.get('favorites', 0),
            'like_count': video_data.get('like', 0),
            'duration': video_data.get('duration', ''),
            'pubdate': video_data.get('pubdate', 0),
            'description': video_data.get('description', ''),
            'tags': video_data.get('tag', ''),
            'keyword_folder': keyword,
            'category': category
        }

    def process_json_file(self, file_path: str, keyword: str, category: str) -> List[Dict[str, Any]]:
        """处理单个JSON文件并提取视频数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查JSON结构并获取视频列表
            videos = data.get('data', {}).get('result', [])
            if not videos:
                return []
            
            # 提取每个视频的特征
            return [self.extract_video_features(video, keyword, category) 
                   for video in videos if isinstance(video, dict)]
        
        except Exception as e:
            print(f"处理文件出错 {file_path}: {str(e)}")
            return []

    def process_all_data(self) -> pd.DataFrame:
        """处理所有文件夹和JSON文件"""
        all_video_data = []
        keywords = self.get_folder_names()
        
        # 使用tqdm显示处理进度
        for keyword in tqdm(keywords, desc="处理关键词文件夹"):
            keyword_dir = os.path.join(self.search_results_dir, keyword)
            
            # 处理每个分类
            for category in self.categories:
                category_dir = os.path.join(keyword_dir, category)
                if not os.path.exists(category_dir):
                    continue
                
                # 处理分类下的所有JSON文件
                for file_name in os.listdir(category_dir):
                    if not file_name.endswith('.json'):
                        continue
                        
                    file_path = os.path.join(category_dir, file_name)
                    video_data = self.process_json_file(file_path, keyword, category)
                    all_video_data.extend(video_data)
        
        # 转换为DataFrame并处理数据
        df = pd.DataFrame(all_video_data)
        
        # 转换时间戳为日期时间
        if 'pubdate' in df.columns:
            df['pubdate'] = pd.to_datetime(df['pubdate'], unit='s')
            
        # 确保数值列为数值类型
        numeric_columns = ['play_count', 'danmaku_count', 'comment_count', 
                         'favorite_count', 'like_count', 'mid']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df

def main():
    # 设置数据目录路径
    base_dir = "./data"
    
    # 创建处理器实例
    processor = VideoDataProcessor(base_dir)
    
    # 处理所有数据
    print("开始处理视频数据...")
    df = processor.process_all_data()
    
    # 保存结果
    output_file = os.path.join(base_dir, "video_data_analysis.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n数据处理完成！共处理 {len(df)} 条视频记录")
    print(f"结果已保存至: {output_file}")
    
    # 显示数据统计信息
    print("\n数据统计:")
    print(f"总视频数: {len(df)}")
    print(f"唯一UP主数: {df['mid'].nunique()}")
    print("\n每个关键词的视频数:")
    print(df['keyword_folder'].value_counts())
    print("\n每个分类的视频数:")
    print(df['category'].value_counts())

if __name__ == "__main__":
    main()