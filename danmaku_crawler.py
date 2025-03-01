# danmaku_crawler.py
import os
import json
import time
import random
import asyncio
import aiohttp
import datetime
from tqdm import tqdm
from headers_pool import HeadersPool
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

class DanmakuCrawler:
    def __init__(self, base_dir="./data"):
        # 基本配置
        self.base_dir = base_dir
        self.danmaku_dir = os.path.join(base_dir, "弹幕数据")
        self.cid_mapping_file = os.path.join(base_dir, "视频CID映射.json")
        
        # 爬取起始位置配置
        self.start_index = 0  # 从第几条数据开始爬取
        
        # 请求头池
        self.headers_pool = HeadersPool()
        
        # 代理配置 (使用时替换为你的隧道代理信息)
        self.proxy_config = {
            "host": "your-proxy-host.com",
            "port": "12345",
            "user": "your-username",
            "pass": "your-password"
        }
        
        # 请求配置
        self.max_retries = 3  # 最大重试次数
        self.concurrent_requests = 5  # 并发请求数量
        self.request_timeout = 10  # 请求超时时间(秒)
        self.min_delay = 0.18  # 最小请求间隔(秒)
        self.max_delay = 0.22  # 最大请求间隔(秒)
        
        # 确保弹幕保存目录存在
        if not os.path.exists(self.danmaku_dir):
            os.makedirs(self.danmaku_dir)
    
    async def create_session(self):
        """创建配置了代理的aiohttp会话"""
        # 配置代理验证信息
        proxy_url = f"http://{self.proxy_config['user']}:{self.proxy_config['pass']}@{self.proxy_config['host']}:{self.proxy_config['port']}"
        
        # 更完整的请求头，更好地模拟浏览器行为
        headers = self.headers_pool.get_random_headers()
        
        # 添加禁用缓存的请求头
        headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        
        # 创建连接会话
        session = aiohttp.ClientSession(headers=headers)
        return session, proxy_url
    
    async def get_segment_danmaku(self, session, cid, segment_index=1, aid=None, proxy_url=None, rate_limiter=None):
        """获取指定CID和分段的弹幕数据"""
        url = 'https://api.bilibili.com/x/v2/dm/web/seg.so'
        params = {
            'type': 1,
            'oid': cid,
            'segment_index': segment_index
        }
        
        if aid:
            params['pid'] = aid
        
        # 等待获取令牌，控制请求速率
        if rate_limiter:
            await rate_limiter.acquire()
        
        # 添加随机延迟，使请求更自然
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
        
        for retry in range(self.max_retries):
            try:
                async with session.get(
                    url, 
                    params=params, 
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        print(f"  HTTP错误: {response.status} (CID: {cid}, 分段: {segment_index}, 重试: {retry+1}/{self.max_retries})")
                        # 服务器错误时增加等待时间
                        if response.status >= 500:
                            await asyncio.sleep(1 * (retry + 1))
                        # 客户端错误，可能是请求过于频繁
                        elif response.status >= 400:
                            await asyncio.sleep(2 * (retry + 1))
            except Exception as e:
                print(f"  获取弹幕时发生异常: {str(e)[:100]} (CID: {cid}, 分段: {segment_index}, 重试: {retry+1}/{self.max_retries})")
                await asyncio.sleep(1 * (retry + 1))  # 出错后等待，避免立即重试
        
        print(f"  达到最大重试次数，无法获取 CID: {cid}, 分段: {segment_index}")
        return None
    
    async def save_raw_danmaku(self, session, video_info, rate_limiter, proxy_url, max_segments=100, pbar=None):
        """保存指定视频的所有分段弹幕数据"""
        cid = video_info.get('cid_info', {}).get('main_cid')
        title = video_info.get('title', '')
        aid = video_info.get('aid')
        bvid = video_info.get('bvid')
        
        if not cid:
            print(f"视频信息缺少CID: {title}")
            if pbar:
                pbar.update(1)
            return None
        
        # 安全处理视频标题，用于文件名
        safe_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in title])
        safe_title = safe_title[:50]  # 限制长度
        
        # 创建视频专属目录
        video_dir = os.path.join(self.danmaku_dir, f"{aid}")
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
            segment_data = await self.get_segment_danmaku(
                session, cid, segment_index, aid, proxy_url, rate_limiter
            )
            
            if segment_data and len(segment_data) > 40:  # 确保响应内容有效
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
        
        # 保存元数据到JSON
        metadata_file = os.path.join(video_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"成功获取 {successfully_fetched} 个分段弹幕，元数据已保存至 {metadata_file}")
        if pbar:
            pbar.update(1)
        return metadata
    
    async def process_video_batch(self, videos, session, rate_limiter, proxy_url, pbar):
        """处理一批视频的异步任务"""
        tasks = []
        for video_info in videos:
            task = asyncio.create_task(
                self.save_raw_danmaku(session, video_info, rate_limiter, proxy_url, pbar=pbar)
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果，计算成功数
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        return success_count
    
    async def process_cid_mapping_async(self):
        """异步处理CID映射文件中的所有视频"""
        if not os.path.exists(self.cid_mapping_file):
            print(f"错误: CID映射文件不存在: {self.cid_mapping_file}")
            return
        
        # 加载CID映射
        with open(self.cid_mapping_file, 'r', encoding='utf-8') as f:
            video_mapping = json.load(f)
        
        videos_to_process = list(video_mapping.values())
        total_videos = len(videos_to_process)
        
        # 从指定的索引开始处理
        if self.start_index >= total_videos:
            print(f"错误: 起始索引 {self.start_index} 超出视频总数 {total_videos}")
            return
        
        videos_to_process = videos_to_process[self.start_index:]
        videos_to_process_count = len(videos_to_process)
        
        print(f"加载了 {total_videos} 个视频的CID映射，将从第 {self.start_index} 条开始处理，共 {videos_to_process_count} 个视频")
        
        # 创建会话和令牌桶限流器
        session, proxy_url = await self.create_session()
        rate_limiter = RateLimiter(self.concurrent_requests)  # 控制整体速率
        
        # 创建进度条
        pbar = tqdm(total=videos_to_process_count, desc="处理视频")
        
        try:
            # 将视频分成小批次处理
            batch_size = self.concurrent_requests
            total_success = 0
            
            for i in range(0, videos_to_process_count, batch_size):
                batch = videos_to_process[i:i+batch_size]
                success_count = await self.process_video_batch(batch, session, rate_limiter, proxy_url, pbar)
                total_success += success_count
                
                # 每处理一批次，报告进度
                current_progress = min(i+batch_size, videos_to_process_count)
                print(f"\n已处理: {current_progress}/{videos_to_process_count} 视频 (全局索引: {self.start_index + current_progress}/{total_videos})，成功: {total_success}")
                
                # 保存进度到文件，以便中断后可以继续
                progress_file = os.path.join(self.base_dir, "crawler_progress.json")
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'last_processed_index': self.start_index + current_progress - 1,
                        'total_videos': total_videos,
                        'success_count': total_success,
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }, f, ensure_ascii=False, indent=2)
        
        finally:
            # 确保会话被关闭
            await session.close()
            pbar.close()
        
        print(f"\n处理完成! 总计处理 {videos_to_process_count} 个视频 (从第 {self.start_index} 条开始)，{total_success} 个成功")


# 限制请求频率的令牌桶
class RateLimiter:
    def __init__(self, rate_limit=5):
        self.rate_limit = rate_limit      # 每秒请求数
        self.tokens = rate_limit          # 当前可用令牌数
        self.last_check = time.time()     # 上次更新令牌的时间
        self.lock = asyncio.Lock()        # 异步锁，用于令牌更新
    
    async def acquire(self):
        """获取一个令牌，如果没有令牌则等待"""
        while True:
            async with self.lock:
                now = time.time()
                # 计算经过的时间，恢复令牌
                time_passed = now - self.last_check
                self.tokens = min(self.rate_limit, self.tokens + time_passed * self.rate_limit)
                self.last_check = now
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            
            # 如果没有足够令牌，等待一小段时间再试
            await asyncio.sleep(0.05)


async def main_async():
    """异步主函数"""
    crawler = DanmakuCrawler()
    print("B站视频弹幕异步爬取工具")
    print("=" * 40)
    print(f"本工具将从CID映射文件中读取视频信息，从第 {crawler.start_index} 条开始，并使用异步方式获取每个视频的实时弹幕")
    
    # 确认CID映射文件存在
    if not os.path.exists(crawler.cid_mapping_file):
        print(f"错误: CID映射文件不存在: {crawler.cid_mapping_file}")
        return
    
    # 确认代理信息已填写
    if (crawler.proxy_config["user"] == "your-username" or 
        crawler.proxy_config["pass"] == "your-password"):
        print("警告: 未配置代理信息，请在代码中正确设置代理隧道的用户名和密码")
    
    await crawler.process_cid_mapping_async()


def main():
    """启动异步主函数"""
    # 在Windows上需要使用特定的事件循环策略
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行异步主函数
    asyncio.run(main_async())


if __name__ == "__main__":
    # 安装必要的库
    # pip install aiohttp tqdm
    main()