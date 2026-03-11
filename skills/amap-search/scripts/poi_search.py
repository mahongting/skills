#!/usr/bin/env python3
"""
高德地图 POI 搜索脚本
用法: python poi_search.py <command> [options]
"""

import argparse
import json
import math
import urllib.parse
import urllib.request
import sys


def ip_location(key, ip=None):
    """IP定位 - 获取用户当前所在城市"""
    base_url = "https://restapi.amap.com/v3/ip"
    
    params = {
        "key": key,
        "output": "json"
    }
    
    if ip:
        params["ip"] = ip
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"status": "0", "info": str(e)}


def search_poi(key, keyword, city=None, location=None, radius=5000, page=1, offset=20):
    """关键字搜索POI"""
    base_url = "https://restapi.amap.com/v3/place/text"
    
    params = {
        "key": key,
        "keywords": keyword,
        "offset": offset,
        "page": page,
        "extensions": "all",
        "output": "json"
    }
    
    if city:
        params["city"] = city
    
    if location:
        params["citylimit"] = "true"
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"status": "0", "info": str(e)}


def search_nearby(key, location, radius, keyword, page=1, offset=20):
    """周边搜索POI"""
    base_url = "https://restapi.amap.com/v3/place/around"
    
    params = {
        "key": key,
        "location": location,
        "radius": radius,
        "keywords": keyword,
        "offset": offset,
        "page": page,
        "extensions": "all",
        "output": "json"
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"status": "0", "info": str(e)}


def geocode(key, address, city=None):
    """地理编码 - 地址转坐标"""
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    
    params = {
        "key": key,
        "address": address,
        "output": "json"
    }
    
    if city:
        params["city"] = city
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"status": "0", "info": str(e)}


def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点之间的距离（米）"""
    R = 6371000  # 地球半径（米）
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def format_ip_results(data, json_output=False):
    """格式化IP定位结果"""
    if data.get("status") != "1":
        msg = f"查询失败: {data.get('info', '未知错误')}"
        if json_output:
            return {"error": msg}
        print(msg)
        return None
    
    province = data.get("province", "未知")
    city = data.get("city", "未知")
    adcode = data.get("adcode", "")
    
    result = {"province": province, "city": city, "adcode": adcode}
    
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"您的当前位置: {province} {city}")
        print(f"城市代码: {adcode}")
        print()
    
    return result


def format_poi_results(data, user_location=None, json_output=False):
    """格式化POI搜索结果"""
    if data.get("status") != "1":
        msg = f"搜索失败: {data.get('info', '未知错误')}"
        if json_output:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return
    
    pois = data.get("pois", [])
    if not pois:
        msg = "未找到相关结果"
        if json_output:
            print(json.dumps({"results": [], "count": 0}, ensure_ascii=False))
        else:
            print(msg)
        return
    
    count = data.get("count", len(pois))
    
    results = []
    for poi in pois[:10]:
        name = poi.get("name", "")
        address = poi.get("address", "")
        location = poi.get("location", "")
        telephone = poi.get("tel", "")
        province = poi.get("province", "")
        city = poi.get("city", "")
        district = poi.get("district", "")
        
        # 计算距离（如果是关键字搜索，需要手动计算）
        distance = poi.get("distance", None)
        if not distance and user_location and location:
            try:
                user_lat, user_lon = map(float, user_location.split(","))
                poi_lat, poi_lon = map(float, location.split(","))
                dist = calculate_distance(user_lat, user_lon, poi_lat, poi_lon)
                distance = int(dist)
            except:
                pass
        
        # 格式化距离
        distance_str = ""
        if distance:
            try:
                d = int(distance)
                if d >= 1000:
                    distance_str = f"{d/1000:.1f}公里"
                else:
                    distance_str = f"{d}米"
            except:
                distance_str = str(distance)
        
        item = {
            "name": name,
            "address": f"{province}{city}{district}{address}" if address else f"{province}{city}{district}",
            "location": location,
            "telephone": telephone
        }
        if distance_str:
            item["distance"] = distance_str
        
        results.append(item)
    
    output = {"results": results, "count": count}
    
    if json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"共找到 {count} 个结果:\n")
        for i, item in enumerate(results, 1):
            print(f"{i}. {item['name']}")
            print(f"   地址: {item['address']}")
            if item.get("distance"):
                print(f"   距离: {item['distance']}")
            if item["telephone"]:
                print(f"   电话: {item['telephone']}")
            print()


def format_geocode_results(data, json_output=False):
    """格式化地理编码结果"""
    if data.get("status") != "1":
        msg = f"查询失败: {data.get('info', '未知错误')}"
        if json_output:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return
    
    geocodes = data.get("geocodes", [])
    if not geocodes:
        msg = "未找到该地址的坐标"
        if json_output:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(msg)
        return
    
    results = []
    for gc in geocodes:
        results.append({
            "address": f"{gc.get('province', '')}{gc.get('city', '')}{gc.get('district', '')}{gc.get('township', '')}",
            "location": gc.get("location", ""),
            "level": gc.get("level", "")
        })
    
    if json_output:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"地址: {item['address']}")
            print(f"坐标: {item['location']}")
            print(f"层级: {item['level']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="高德地图 POI 搜索工具")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # ip 子命令
    ip_parser = subparsers.add_parser("ip", help="IP定位 - 获取当前位置")
    ip_parser.add_argument("--key", required=True, help="高德API Key")
    ip_parser.add_argument("--ip", help="指定IP，不填则自动获取")
    
    # poi 子命令
    poi_parser = subparsers.add_parser("poi", help="关键字搜索POI")
    poi_parser.add_argument("--key", required=True, help="高德API Key")
    poi_parser.add_argument("--keyword", required=True, help="搜索关键词")
    poi_parser.add_argument("--city", help="城市名称")
    poi_parser.add_argument("--location", help="经纬度坐标，格式: 经度,纬度，用于计算距离")
    poi_parser.add_argument("--radius", type=int, default=5000, help="搜索半径(米)")
    poi_parser.add_argument("--page", type=int, default=1, help="页码")
    poi_parser.add_argument("--offset", type=int, default=20, help="每页数量")
    
    # geo 子命令
    geo_parser = subparsers.add_parser("geo", help="地理编码 - 地址转坐标")
    geo_parser.add_argument("--key", required=True, help="高德API Key")
    geo_parser.add_argument("--address", required=True, help="地址")
    geo_parser.add_argument("--city", help="城市名称")
    
    args = parser.parse_args()
    
    # 通用参数
    json_output = args.json
    
    if args.command == "ip":
        data = ip_location(args.key, args.ip)
        format_ip_results(data, json_output)
        
    elif args.command == "poi":
        if args.location:
            # 周边搜索
            data = search_nearby(args.key, args.location, args.radius, args.keyword, args.page, args.offset)
        else:
            # 关键字搜索
            data = search_poi(args.key, args.keyword, args.city, args.location, args.radius, args.page, args.offset)
        format_poi_results(data, args.location, json_output)
        
    elif args.command == "geo":
        data = geocode(args.key, args.address, args.city)
        format_geocode_results(data, json_output)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
