# Bilibili视频与弹幕爬虫

这是一个完整的B站视频搜索与弹幕数据采集工具集，用于研究和分析B站视频内容与用户互动行为。本工具支持基于关键词搜索视频，获取视频详细信息，并高效爬取和解析弹幕数据，为B站内容分析提供了全面的数据收集解决方案。

## 项目结构
```
bilibili-crawler/
│
├── headers_pool.py          # 请求头池管理
├── bilibili_search.py       # 视频搜索模块
├── video_cid_mapper.py      # 视频CID映射工具
├── danmaku_crawler.py       # 弹幕异步爬取引擎
├── danmaku_parser.py        # 弹幕解析基础功能
├── danmaku_extractor.py     # 弹幕信息提取与数据集生成
├── video_info_processor.py  # 视频信息整合与处理
├── dm_pb2.py                # 弹幕协议Protobuf定义文件
└── requirements.txt         # 项目依赖清单
```

## 功能模块详解

### 1. 请求头池管理 (`headers_pool.py`)

这个模块提供了随机生成浏览器请求头的功能，有效避免爬虫被检测和封禁。

**核心特性：**
- 支持多种主流浏览器的请求头模拟（Chrome、Firefox、Edge等）
- 支持桌面和移动设备的UA标识
- 随机选择功能确保每次请求使用不同的请求头

**使用提示：**
- 可以根据需要扩展请求头池，增加更多的浏览器和设备类型
- 对反爬虫严格的网站，建议增加更多的请求头变种

---

### 2. 视频搜索 (`bilibili_search.py`)

负责基于关键词和分类在B站搜索视频，并保存搜索结果。

**核心特性：**
- 支持多关键词批量搜索
- 支持按分区（知识、生活、美食等）搜索
- 支持多页结果爬取（最多50页）
- 内置智能休眠机制，避免请求过快触发反爬措施

**关键代码与参数：**
```python
keywords = ["关键词1", "关键词2", "关键词3"]
category_dict = {"知识": 36, "生活": 160, "美食": 211}
order = "dm"  # 可选: "dm"（弹幕量排序）, "pubdate"（最新发布）, "click"（最多播放）
```

**使用提示：**
- 在正式批量爬取前，建议先用少量关键词测试
- 如需大规模爬取，建议增加更长的休眠时间
- 搜索结果保存在按关键词和分类组织的文件夹结构中，便于后续处理

---

### 3. 视频CID映射 (`video_cid_mapper.py`)

负责从搜索结果中提取视频ID，并获取视频的CID（内容ID）信息。CID是获取弹幕的必要参数。

**核心特性：**
- 自动提取视频URL中的AV号或BV号
- 通过B站API获取视频的CID和分集信息
- 支持断点续取，自动跳过已处理的视频
- 带进度显示和错误重试机制

**使用提示：**
- 映射文件会保存为JSON格式，包含详细的视频信息
- 如果视频有多P，会保存所有分P的CID信息
- 处理大量视频时，可能需要较长时间，请耐心等待

---

### 4. 弹幕爬取 (`danmaku_crawler.py`)

**核心特性：**
- 基于`asyncio`和`aiohttp`实现异步并发爬取，大幅提高效率
- 支持从任意位置开始断点续爬
- 自动分段获取视频弹幕（每段对应视频的6分钟）
- 内置令牌桶算法实现精确的请求频率控制

**技术亮点：**
- `RateLimiter`类：实现了令牌桶算法，精确控制请求频率
- 异步批处理：将任务分批并发执行，兼顾效率和稳定性
- 完善的元数据记录：为每个视频创建`metadata.json`，记录弹幕段信息

**使用示例：**
```python
python danmaku_crawler.py
```

---

### 5. 弹幕解析 (`danmaku_parser.py`)

**核心功能：**
- 解析B站弹幕的二进制格式（基于protobuf协议）
- 提取弹幕的时间点、内容、颜色、模式等信息

**使用示例：**
```python
parser = DanmakuParser()
danmaku_seg = parser.parse_danmaku_bin("/path/to/segment_1.bin")
parser.print_danmaku_info(danmaku_seg)
```

---

### 6. 弹幕信息提取 (`danmaku_extractor.py`)

**核心特性：**
- 批量处理所有爬取的弹幕文件
- 生成CSV格式的完整弹幕数据集

**数据字段：**
| 字段名  | 含义 |
|---------|------|
| progress | 弹幕出现时间（秒） |
| content  | 弹幕内容 |
| mode     | 弹幕模式（滚动、底部、顶部等） |
| color    | 弹幕颜色 |
| video_id | 视频ID |
| video_title | 视频标题 |

**使用示例：**
```bash
python danmaku_extractor.py
```

---

### 7. 视频信息整合 (`video_info_processor.py`)

**核心特性：**
- 处理搜索结果并清洗数据
- 生成完整的视频元数据集
- 输出为CSV格式，便于数据分析

**关键字段：**
| 字段名  | 含义 |
|---------|------|
| video_id | 视频ID |
| title    | 视频标题 |
| author   | UP主 |
| views    | 播放量 |
| danmaku  | 弹幕数 |
| likes    | 点赞数 |

**使用示例：**
```bash
python video_info_processor.py
```

---

## 安装与依赖

```bash
pip install -r requirements.txt
```

**主要依赖库：**
- `requests`：HTTP请求
- `numpy`：数学运算
- `pandas`：数据处理
- `aiohttp`：异步HTTP请求
- `protobuf`：弹幕解析

---

## 使用流程

1. **搜索视频**
   ```bash
   python bilibili_search.py
   ```
2. **生成视频CID映射**
   ```bash
   python video_cid_mapper.py
   ```
3. **爬取弹幕数据**
   ```bash
   python danmaku_crawler.py
   ```
4. **解析弹幕与生成数据集**
   ```bash
   python danmaku_extractor.py
   ```
5. **生成视频信息数据集**
   ```bash
   python video_info_processor.py
   ```

---

## 注意事项与最佳实践

- **请求频率控制**：建议每秒不超过5次，避免IP被封。
- **断点续爬**：所有模块均支持断点续爬，可根据进度文件调整`start_index`参数。
- **代理使用**：大规模爬取建议使用代理，以避免IP封锁。

---

## 参考代码
https://github.com/SocialSisterYi/bilibili-API-collect


## License

MIT

**免责声明：** 本工具仅供学习和研究使用，请勿用于商业目的。尊重B站的使用条款和规定，合理使用爬虫。注意保护用户隐私，不要过度收集和分析个人信息。

