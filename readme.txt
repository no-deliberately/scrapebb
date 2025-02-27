# BiliBili 弹幕爬虫工具

这个项目提供了一套工具，用于爬取 BiliBili 视频的弹幕数据。通过利用视频 CID 信息，可以获取并保存完整的分段弹幕数据。

## 功能特点

- 支持根据视频 CID 获取所有分段的弹幕数据
- 保存原始二进制弹幕文件，便于后续分析
- 自动生成详细的元数据，包括分段信息和时间戳
- 提供多种筛选方式：全部处理、指定数量、关键词过滤、分类过滤
- 采用随机延时策略，避免请求过于频繁

## 项目文件说明

- `scraping_via_cids.py` - 使用已获取的 CID 爬取弹幕的主程序
- `mapping_from_av_to_cid.py` - 从视频 AV 号映射获取 CID 信息
- `exploit_searching_api.py` - 通过搜索 API 获取视频信息
- `readme.txt` - 基本说明文档

## 使用方法

### 环境准备

```bash
# 安装所需依赖
pip install requests tqdm
```

### 基本使用流程

1. 首先使用 `mapping_from_av_to_cid.py` 生成视频 CID 映射文件
2. 然后运行 `scraping_via_cids.py` 开始爬取弹幕数据
3. 爬取的弹幕会按视频分类保存在指定目录中

### 代码示例

```python
# 设置基本配置
base_dir = r"你的保存目录"
danmaku_dir = os.path.join(base_dir, "弹幕数据")
cid_mapping_file = os.path.join(base_dir, "视频CID映射.json")

# 运行主程序
process_cid_mapping()
```

## 数据说明

爬取的数据会以以下结构保存：

```
弹幕数据/
  ├── aid_视频标题/
  │     ├── segment_1.bin  # 第一段弹幕数据
  │     ├── segment_2.bin  # 第二段弹幕数据
  │     └── metadata.json  # 元数据信息
  └── ...
```

元数据包含视频标题、AID、BVID、CID、获取时间和分段信息等重要数据。

## 注意事项

- 本工具仅用于学习和研究，请勿用于商业用途
- 请合理控制爬取频率，避免对 B站 服务器造成压力
- 爬取的弹幕数据版权归 BiliBili 和内容创作者所有

## 开发计划

- [ ] 添加弹幕内容解析功能
- [ ] 实现弹幕数据可视化分析
- [ ] 支持更多筛选条件和导出格式

## 贡献

欢迎提交 Issue 或 Pull Request 来完善这个项目。

## 许可

MIT License
 