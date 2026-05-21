# fetch_schedule.py
import json
import os
from datetime import datetime
import requests

# ---------- 配置 ----------
# 设置为 True 时使用 Mock 数据，False 时调用真实 API
USE_MOCK = False  # 改为 False 使用真实 API

# 真实 API 配置
REAL_API_URL = "https://iadr.isoftstone.com/iac/api/clock/sys-clock-record/getClockInfo"

# API 请求头配置
API_HEADERS = {
    "sec-ch-ua-platform": "Android",
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; V2352GA Build/BP2A.250605.031.A3; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/146.0.7680.177 Mobile Safari/537.36;ipsa_android",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "X-Requested-With": "com.isoftstone.client.ipsa",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 从 GitHub Secrets 读取敏感信息
ISSCLOCK_CLIENT_TOKEN = os.environ.get("ISSCLOCK_CLIENT_TOKEN", "")
COOKIE = os.environ.get("COOKIE", "")

# 如果 token 或 cookie 存在，添加到请求头
if ISSCLOCK_CLIENT_TOKEN:
    API_HEADERS["issclock-client-token"] = ISSCLOCK_CLIENT_TOKEN
if COOKIE:
    API_HEADERS["Cookie"] = COOKIE

# POST 请求的 body
REQUEST_BODY = {}

def fetch_work_schedule():
    """
    调用外部 API 获取上班时间和下班时间。
    返回: (work_start, work_end, has_start, has_end)
    """
    # 使用 Mock 数据
    if USE_MOCK:
        print("🔧 使用 Mock 数据模式")
        work_start, work_end, has_start, has_end = get_mock_schedule()
        return work_start, work_end, has_start, has_end
    
    # 调用真实 API
    print("🌐 调用真实 API")
    print(f"📍 API URL: {REAL_API_URL}")
    
    try:
        response = requests.post(
            REAL_API_URL, 
            headers=API_HEADERS, 
            json=REQUEST_BODY,
            timeout=15
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        response.raise_for_status()
        
        # 解析 JSON 响应
        data = response.json()
        print(f"📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 检查 API 是否成功
        if not data.get("flag", False):
            print(f"⚠️ API 返回失败: {data.get('msg', 'Unknown error')}")
            return "09:00", "18:00", False, False
        
        # 解析打卡记录
        records = data.get("data", [])
        work_start = "未打卡"
        work_end = "未打卡"
        has_start = False
        has_end = False
        
        for record in records:
            sort = record.get("sort")
            clock_time = record.get("clockTime", "")
            
            # 提取 HH:MM 格式
            if clock_time and ":" in clock_time:
                time_formatted = clock_time[:5]  # 取前5个字符 "HH:MM"
            else:
                time_formatted = clock_time
            
            if sort == 1:  # 上班时间
                work_start = time_formatted
                has_start = True
                print(f"✅ 找到上班打卡时间: {work_start}")
            elif sort == 2:  # 下班时间
                work_end = time_formatted
                has_end = True
                print(f"✅ 找到下班打卡时间: {work_end}")
        
        # 根据打卡情况输出提示
        if not has_start:
            print("⚠️ 未找到上班打卡记录")
        if not has_end:
            print("⚠️ 未找到下班打卡记录")
        
        return work_start, work_end, has_start, has_end
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        print("使用默认时间作为降级方案")
        return "09:00", "18:00", True, True
    except Exception as e:
        print(f"❌ 解析响应失败: {e}")
        return "09:00", "18:00", True, True

def get_mock_schedule():
    """生成 mock 的上下班时间数据（用于测试）"""
    import random
    
    # 随机模拟打卡状态
    has_start = random.choice([True, True, True, False])  # 75% 概率有上班打卡
    has_end = random.choice([True, True, True, False])    # 75% 概率有下班打卡
    
    if has_start:
        start_hour = random.randint(8, 9)
        start_minute = random.choice([0, 15, 30, 45])
        work_start = f"{start_hour:02d}:{start_minute:02d}"
    else:
        work_start = "未打卡"
    
    if has_end:
        end_hour = random.randint(17, 19)
        end_minute = random.choice([0, 15, 30, 45])
        work_end = f"{end_hour:02d}:{end_minute:02d}"
    else:
        work_end = "未打卡"
    
    print(f"📊 Mock 数据 - 上班: {work_start}, 下班: {work_end}")
    print(f"📊 打卡状态 - 上班: {'已打卡' if has_start else '未打卡'}, 下班: {'已打卡' if has_end else '未打卡'}")
    
    return work_start, work_end, has_start, has_end

def generate_html(work_start, work_end, has_start, has_end, update_time):
    """生成展示上下班时间的静态 HTML"""
    
    # 根据打卡状态设置不同的样式
    start_style = "" if has_start else "opacity: 0.6; background: #fef2f2;"
    end_style = "" if has_end else "opacity: 0.6; background: #fef2f2;"
    
    start_time_display = work_start if has_start else "未打卡"
    end_time_display = work_end if has_end else "未打卡"
    
    # 未打卡时的特殊标记
    start_badge = "" if has_start else '<span style="font-size: 0.75rem; color: #ef4444; margin-left: 8px;">⚠️ 未打卡</span>'
    end_badge = "" if has_end else '<span style="font-size: 0.75rem; color: #ef4444; margin-left: 8px;">⚠️ 未打卡</span>'
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日上下班时间</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #1e293b;
            text-align: center;
            min-height: 100vh;
        }}
        .card {{
            background: white;
            border-radius: 32px;
            padding: 2rem;
            box-shadow: 0 20px 35px -10px rgba(0,0,0,0.2);
            margin-top: 5vh;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #0f172a;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}
        .time-block {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        .time-item {{
            background: #f1f5f9;
            border-radius: 24px;
            padding: 1.2rem 1.8rem;
            min-width: 160px;
            transition: transform 0.2s;
        }}
        .time-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .label {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #475569;
            margin-bottom: 0.5rem;
        }}
        .time {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 0.5rem;
            color: #0f172a;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .status-badge {{
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 12px;
            background: #e2e8f0;
            color: #475569;
            margin-left: 8px;
        }}
        .update-info {{
            margin-top: 2rem;
            font-size: 0.8rem;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            padding-top: 1rem;
        }}
        .warning {{
            background: #fef2f2;
            border-left: 3px solid #ef4444;
            padding: 0.5rem;
            margin-top: 1rem;
            font-size: 0.8rem;
            color: #991b1b;
        }}
        footer {{
            margin-top: 2rem;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.8);
        }}
        @media (max-width: 480px) {{
            .time-block {{ gap: 1rem; }}
            .time-item {{ padding: 0.8rem 1rem; min-width: 130px; }}
            .time {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🏢 今日工作时间</h1>
        <div class="subtitle">打卡记录</div>
        
        <div class="time-block">
            <div class="time-item" style="{start_style}">
                <div class="label">⏰ 上班时间</div>
                <div class="time">
                    {start_time_display}
                    {start_badge}
                </div>
            </div>
            <div class="time-item" style="{end_style}">
                <div class="label">🏠 下班时间</div>
                <div class="time">
                    {end_time_display}
                    {end_badge}
                </div>
            </div>
        </div>
        
        {f'<div class="warning">⚠️ 提示：今日打卡记录不完整，请及时打卡！</div>' if not (has_start and has_end) else ''}
        
        <div class="update-info">
            📅 数据更新时间：{update_time}<br>
            ⏰ 每日自动刷新（北京时间 9:00）<br>
            📊 状态：{'✅ 今日打卡完整' if (has_start and has_end) else '⚠️ 打卡记录不完整'}
        </div>
    </div>
    <footer>
        Powered by GitHub Actions & Python
    </footer>
</body>
</html>"""
    return html_content

def main():
    print("=" * 50)
    print("🚀 开始生成静态页面")
    print(f"📁 当前工作目录: {os.getcwd()}")
    
    # 获取上下班时间
    work_start, work_end, has_start, has_end = fetch_work_schedule()
    
    # 生成时间戳（北京时间）
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz)
    beijing_time_str = beijing_time.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 生成 HTML
    html = generate_html(work_start, work_end, has_start, has_end, beijing_time_str)
    
    # 创建 public 目录
    os.makedirs("public", exist_ok=True)
    
    # 写入 index.html
    index_path = "public/index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 同时保存 JSON 格式的数据（便于调试）
    json_data = {
        "update_time": beijing_time_str,
        "work_start": work_start,
        "work_end": work_end,
        "has_start": has_start,
        "has_end": has_end,
        "complete": has_start and has_end
    }
    with open("public/data.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 成功生成 {index_path}")
    print(f"✅ 成功生成 public/data.json")
    print(f"📊 上班时间: {work_start} ({'已打卡' if has_start else '未打卡'})")
    print(f"📊 下班时间: {work_end} ({'已打卡' if has_end else '未打卡'})")
    print("=" * 50)

if __name__ == "__main__":
    main()
