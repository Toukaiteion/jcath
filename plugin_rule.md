# 搜刮插件管理模块设计文档

## 一、概述

本文档设计一个用于管理媒体内容搜刮插件的模块，允许用户安装、配置和运行Python搜刮脚本来自动获取媒体元数据。

**插件形式：打包插件（自包含）**
- 插件打包时已经包含所有依赖和虚拟环境
- 系统只需管理配置和执行，无需处理Python依赖
- 插件可执行文件位于插件目录中（如 `bin/scraper` 或 `run.sh`）

## 二、插件定义与运行标准

### 2.1 插件输入输出标准

**标准接口：**

插件通过标准化的JSON格式进行输入输出通信。

#### 输入格式 (stdin)
```json
{
  "action": "scrape",
  "source_dir": "/path/to/movie/directory",
  "config": {
    "language": "zh-CN",
    "poster_quality": "high",
    "custom_fields": {}
  },
  "media_info": {
    "title": "电影标题（可选，用于匹配）",
    "year": "2024"
  }
}
```

#### 输出格式 (stdout)
```json
{
  "status": "success",
  "message": "Scraping completed",
  "metadata": {
    "title": "电影标题",
    "original_title": "原始标题",
    "year": "2024",
    "release_date": "2024-01-01",
    "summary": "剧情简介",
    "runtime": 120,
    "studio": "制作公司",
    "maker": "发行商",
    "num": "唯一标识号",
    "tags": ["标签1", "标签2"],
    "actors": ["演员1", "演员2"],
    "images": {
      "poster": "poster.jpg",
      "thumb": "thumb.jpg",
      "fanart": "fanart.jpg"
    }
  },
  "created_files": {
    "nfo": "movie.nfo",
    "poster": "poster.jpg",
    "fanart": "fanart.jpg",
    "screenshots": ["shot1.jpg", "shot2.jpg"]
  },
  "statistics": {
    "total_time_ms": 5000,
    "api_requests": 3
  }
}
```

### 2.2 运行状态通知标准

插件通过stderr输出进度通知，格式为JSON行的progress事件：

```
{"type": "progress", "step": "searching", "message": "Searching for movie...", "percent": 10}
{"type": "progress", "step": "downloading", "message": "Downloading poster...", "percent": 50}
{"type": "progress", "step": "saving", "message": "Saving metadata...", "percent": 80}
```

支持的进度步骤类型：
- `initializing`: 初始化中
- `searching`: 搜索中
- `downloading`: 下载资源中
- `parsing`: 解析数据中
- `saving`: 保存文件中
- `completed`: 完成

### 2.3 插件文件结构

```
plugins/
├── av-mogu/1.0.0/          # 插件目录（插件ID/版本）
│   ├── plugin.json           # 插件定义文件（必需）
│   ├── bin/                 # 可执行文件目录
│   │   ├── scraper          # 主执行程序（Linux/macOS）
│   │   ├── scraper.exe      # 主执行程序（Windows）
│   │   └── python/         # Python虚拟环境（可选，如果需要）
│   ├── README.md            # 说明文档（可选）
│   └── icon.png            # 插件图标（可选）
└── javbus/1.2.0/
    ├── plugin.json
    ├── bin/
    │   └── scraper
    └── ...
```

### 2.4 插件定义文件 (plugin.json)

```json
{
  "id": "av-mogu",
  "name": "AVMOGU搜刮器",
  "version": "1.0.0",
  "description": "从AVMOGU网站获取成人电影元数据",
  "author": "MediaHouse",
  "homepage": "https://github.com/mediahouse/av-mogu-scraper",
  "supported_media_types": ["movie"],
  "supported_languages": ["zh-CN", "en-US"],
  "config_schema": {
    "language": {
      "type": "select",
      "label": "语言",
      "default": "zh-CN",
      "options": [
        {"value": "zh", "label": "中文"},
        {"value": "en", "label": "English"}
      ]
    },
    "poster_quality": {
      "type": "select",
      "label": "海报质量",
      "default": "high",
      "options": [
        {"value": "low", "label": "低"},
        {"value": "medium", "label": "中"},
        {"value": "high", "label": "高"}
      ]
    },
    "download_screenshots": {
      "type": "boolean",
      "label": "下载截图",
      "default": true
    },
    "screenshot_count": {
      "type": "number",
      "label": "截图数量",
      "default": 3,
      "min": 1,
      "max": 10
    }
  },
  "runtime_requirements": {
    "max_execution_time_seconds": 300,
    "min_memory_mb": 128
  },
  "entry_point": "bin/scraper",
  "supported_identifiers": ["num", "filename"]
}
```

### 2.5 插件打包格式

支持的打包格式：
- `.tar.gz` - Linux/macOS通用格式
- `.zip` - Windows通用格式

打包内容：
- plugin.json（必需）
- bin/ 目录及可执行文件（必需）
- 可选的README.md、icon.png等资源
