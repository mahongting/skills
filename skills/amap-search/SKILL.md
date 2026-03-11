---
name: amap-search
description: 高德地图周边搜索。用于查找指定地点附近的商家、服务设施。当用户询问"某地A附近有没有某地B"时使用，如：查找"科学城附近的汽车4S店"、"公司楼下的停车场"等。支持IP自动定位、关键字搜索、周边搜索、POI详情查询、地理编码。/AMap (Gaode Map) nearby search. Find shops/services near a location, e.g., "car 4S stores near Chengdu Science City". Supports IP location, keyword search, nearby search, POI details, geocoding.
version: 1.0.0
icon: 🗺️
---

# 高德地图周边搜索 (amap-search)

调用高德地图 Web 服务 API 搜索附近地点。

## 触发场景

当用户询问「附近/旁边有没有XX」时使用，例如：
- "帮我查一下附近哪里有洗车店"
- "我家楼下有停车场吗？"
- "公司旁边有药店吗？"

---

# AMap Nearby Search (amap-search)

Call Gaode Map Web Service API to search nearby places.

## When to Use

When users ask "Is there XX near here?", for example:
- "Find car wash shops near me"
- "Any parking lot near my home?"
- "Pharmacy next to my office?"

## 前置条件 / Prerequisites

1. 申请高德 API Key：https://lbs.amap.com/
2. 创建应用 → 添加 Key（选择 Web服务）
3. 免费配额：每天 2000 次

1. Apply for Gaode API Key: https://lbs.amap.com/
2. Create App → Add Key (Web Services)
3. Free quota: 2000 requests/day

## 功能列表 / Features

| 命令/Command | 用途/Usage |
|------|------|
| `ip` | 自动获取用户当前位置（IP定位）/ IP location - get user location |
| `geo` | 地址转坐标 / Geocoding - address to coordinates |
| `poi` | 关键字搜索 / 周边搜索 / Keyword search / Nearby search |

## 使用方式 / Usage

### 1. IP定位 / IP Location

```bash
python3 scripts/poi_search.py ip --key YOUR_API_KEY
```

### 2. 周边搜索 / Nearby Search

```bash
python3 scripts/poi_search.py poi --key YOUR_KEY --location "经度,纬度" --radius 5000 --keyword "洗车店"
```

### 3. 城市搜索 / City Search

```bash
python3 scripts/poi_search.py poi --key YOUR_KEY --city 成都 --keyword "洗车店"
```

## 注意事项 / Notes

- IP定位是**粗略定位**，精确度取决于用户网络（通常到城市级别）
- IP location is **approximate**, accuracy depends on network (usually city-level)
- 周边搜索半径默认 5000 米，最大 50000 米
- Search radius default 5000m, max 50000m
