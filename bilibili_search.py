# bilibili_search.py
import os
import json
import time
import random
import requests
import numpy as np

class BilibiliSearcher:
    def __init__(self):
        # 关键词列表
        self.keywords = []  # 替换为实际关键词列表
        
        # 分类字典 - 键为分类名称，值为tids
        self.category_dict = {
            "知识": 36, 
            "生活": 160, 
            "美食": 211
        }
        
        # 基础路径
        self.base_dir = "./data/search_results"
        
        # 确保基础目录存在
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def save_response(self, keyword, category, page, response_data):
        """保存API响应数据到JSON文件"""
        # 创建关键词目录
        keyword_dir = os.path.join(self.base_dir, keyword)
        if not os.path.exists(keyword_dir):
            os.makedirs(keyword_dir)
        
        # 创建分类目录
        category_dir = os.path.join(keyword_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        
        # 保存文件
        file_path = os.path.join(category_dir, f"{keyword}_{category}_第{page}页.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
        
        print(f"已保存: {file_path}")
    
    def get_random_sleep_time(self):
        """生成一个服从正态分布绝对值的随机休眠时间"""
        # 均值为3秒，标准差为2秒，取绝对值确保为正
        sleep_time = abs(np.random.normal(3, 2))
        # 限制在0.5到5秒之间
        return max(0.5, min(sleep_time, 5))
    
    def search_videos(self):
        """主函数：根据关键词和分类搜索视频"""
        # 设置请求头
        headers = {
            'Referer': 'https://www.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 设置cookies (如需要登录态)
        cookies = {
            'SESSDATA': ''  # 如需登录态，替换为实际SESSDATA值
        }
        
        # 遍历所有关键词
        for keyword in self.keywords:
            print(f"\n开始搜索关键词: {keyword}")
            
            # 遍历所有分类
            for category_name, tid in self.category_dict.items():
                print(f"\n  分类: {category_name} (tid={tid})")
                
                # 设置通用参数
                params = {
                    'search_type': 'video',
                    'keyword': keyword,
                    'order': 'dm',  # 弹幕最多优先
                    'duration': '0',
                    'tids': tid,
                    'page': 1
                }
                
                # 搜索API
                url = 'https://api.bilibili.com/x/web-interface/search/type'
                
                # 执行搜索并保存结果
                self._execute_search(url, params, keyword, category_name, headers, cookies)
    
    def _execute_search(self, url, params, keyword, category_name, headers, cookies):
        """执行搜索操作并保存结果"""
        try:
            # 请求第一页
            response = requests.get(url, params=params, cookies=cookies, headers=headers)
            
            # 检查状态码
            if response.status_code != 200:
                print(f"  错误: HTTP状态码 {response.status_code}")
                return
            
            # 解析响应
            result = response.json()
            
            # 检查API返回的状态
            if result.get('code') != 0:
                print(f"  API错误: {result.get('code')} - {result.get('message')}")
                return
            
            # 保存第一页结果
            self.save_response(keyword, category_name, 1, result)
            
            # 获取总页数
            total_pages = result.get('data', {}).get('numPages', 0)
            total_results = result.get('data', {}).get('numResults', 0)
            print(f"  找到 {total_results} 个结果，共 {total_pages} 页")
            
            # 限制页数，避免请求过多
            max_pages = min(total_pages, 50)  # B站通常最多返回50页
            
            # 请求剩余页面
            for page in range(2, max_pages + 1):
                # 随机休眠，避免请求过于频繁
                sleep_time = self.get_random_sleep_time()
                print(f"  休眠 {sleep_time:.2f} 秒后请求第 {page} 页...")
                time.sleep(sleep_time)
                
                # 更新页码
                params['page'] = page
                
                # 发送请求
                response = requests.get(url, params=params, cookies=cookies, headers=headers)
                
                # 检查状态码
                if response.status_code != 200:
                    print(f"  错误: 第 {page} 页请求失败，HTTP状态码 {response.status_code}")
                    continue
                
                # 解析响应
                result = response.json()
                
                # 检查API返回的状态
                if result.get('code') != 0:
                    print(f"  API错误: 第 {page} 页，{result.get('code')} - {result.get('message')}")
                    continue
                
                # 保存结果
                self.save_response(keyword, category_name, page, result)
            
        except Exception as e:
            print(f"  异常: {str(e)}")
            # 发生异常后等待一段时间再继续
            time.sleep(5)


if __name__ == "__main__":
    # 安装必要的库
    # pip install requests numpy
    
    searcher = BilibiliSearcher()
    print("开始搜索B站视频...")
    searcher.search_videos()
    print("\n所有搜索完成!")