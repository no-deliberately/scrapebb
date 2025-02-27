# Bilibili Video and Danmaku Scraper

This project is a collection of tools to search for videos on Bilibili, extract their video IDs and CIDs, and download danmaku (comments) data.

## Components

The project consists of three main scripts:

1. **exploit_searching_api.py** - Searches for videos on Bilibili using keywords and categories
2. **mapping_from_av_to_cid.py** - Maps video URLs to their CIDs (Comment IDs)
3. **scraping_via_cids.py** - Downloads danmaku data for videos using their CIDs

## Requirements

- Python 3.6+
- Required packages:
  ```
  requests
  numpy
  tqdm
  ```

You can install the required packages with:
```
pip install requests numpy tqdm
```

## Usage

### 1. Search for Videos

First, search for videos using keywords and categories:

```python
python exploit_searching_api.py
```

Before running:
- Edit the `keywords` list with your search terms
- Modify the `category_dict` with desired categories and their corresponding IDs
- Set the `base_dir` path where search results will be saved
- Add your Bilibili SESSDATA cookie for authenticated requests

The script will:
- Search Bilibili for videos matching your keywords and categories
- Save the search results as JSON files organized by keyword and category

### 2. Extract Video CIDs

After collecting search results, extract the CIDs for each video:

```python
python mapping_from_av_to_cid.py
```

Before running:
- Set the `base_dir` to the same directory used in the first script
- The script will create a mapping file named "视频CID映射.json"

### 3. Download Danmaku Data

Finally, download the danmaku data for the videos:

```python
python scraping_via_cids.py
```

The script will:
- Load the CID mapping file created in step 2
- Present options to process all videos, a specific number of videos, filter by keyword, or by category
- Download danmaku data in segments for each selected video
- Save both raw danmaku data and metadata for each video

## Data Structure

The project creates the following directory structure:

```
base_dir/
├── [keyword]/
│   ├── [category]/
│   │   ├── [keyword]_[category]_第1页.json
│   │   ├── [keyword]_[category]_第2页.json
│   │   └── ...
│   └── ...
├── 视频CID映射.json
└── 弹幕数据/
    ├── [aid]_[title]/
    │   ├── segment_1.bin
    │   ├── segment_2.bin
    │   ├── ...
    │   └── metadata.json
    └── ...
```

## Notes

- The scripts include random sleep intervals to avoid being rate-limited by Bilibili
- Each script can be run independently, but they are designed to be used in sequence
- Make sure you have appropriate permissions before scraping data from Bilibili
- Consider Bilibili's terms of service when using these scripts

## Limitations

- The search API is limited to approximately 50 pages per search
- Danmaku data is segmented in 6-minute chunks (segment_index parameter)
- Be respectful of Bilibili's servers and avoid making too many requests in a short time