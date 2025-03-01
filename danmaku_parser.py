# danmaku_parser.py
import sys
import os
from google.protobuf import text_format

# 导入protobuf模块
import dm_pb2 as Danmaku

class DanmakuParser:
    @staticmethod
    def parse_danmaku_bin(bin_file_path):
        """解析单个弹幕二进制文件并返回解析结果"""
        try:
            # 读取二进制文件
            with open(bin_file_path, 'rb') as f:
                binary_data = f.read()
            
            # 解析protobuf数据
            danmaku_seg = Danmaku.DmSegMobileReply()
            danmaku_seg.ParseFromString(binary_data)
            
            # 返回解析结果
            return danmaku_seg
        except Exception as e:
            print(f"解析弹幕文件时出错: {str(e)}")
            return None
    
    @staticmethod
    def print_danmaku_info(danmaku_seg, limit=10):
        """打印弹幕信息摘要"""
        if not danmaku_seg:
            print("未提供有效的弹幕数据")
            return
            
        # 打印摘要
        print(f"成功解析! 共找到 {len(danmaku_seg.elems)} 条弹幕")
        
        # 打印前几条弹幕详情
        for i, elem in enumerate(danmaku_seg.elems[:limit]):
            print(f"\n弹幕 #{i+1}:")
            print(f"时间: {elem.progress/1000:.2f}秒")
            print(f"内容: {elem.content}")
            print(f"模式: {elem.mode}")
            print(f"颜色: {elem.color}")
            print(f"字体大小: {elem.fontsize}")


def main():
    """命令行入口函数"""
    if len(sys.argv) < 2:
        print("用法: python danmaku_parser.py [弹幕二进制文件路径]")
        sys.exit(1)
    
    bin_file_path = sys.argv[1]
    
    parser = DanmakuParser()
    danmaku_seg = parser.parse_danmaku_bin(bin_file_path)
    
    if danmaku_seg:
        parser.print_danmaku_info(danmaku_seg)


if __name__ == "__main__":
    main()