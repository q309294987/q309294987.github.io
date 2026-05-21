# fetch_schedule.py
import json
import os
from datetime import datetime
import requests

# ---------- 配置 ----------
REAL_API_URL = os.environ.get("REAL_API_URL", "")

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

if ISSCLOCK_CLIENT_TOKEN:
    API_HEADERS["issclock-client-token"] = ISSCLOCK_CLIENT_TOKEN
if COOKIE:
    API_HEADERS["Cookie"] = COOKIE

REQUEST_BODY = {}

# 全局变量记录 API 错误信息
api_error = None

def fetch_work_schedule():
    """
    调用外部 API 获取上班时间和下班时间。
    返回: (work_start, work_end, has_start, has_end, error_msg)
    """
    global api_error
    api_error = None
    
    try:
        response = requests.post(
            REAL_API_URL, 
            headers=API_HEADERS, 
            json=REQUEST_BODY,
            timeout=15
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 检查 API 是否成功
        if not data.get("flag", False):
            api_error = data.get('msg', 'API 返回失败')
            return "00:00", "00:00", False, False, api_error
        
        # 解析打卡记录
        records = data.get("data", [])
        work_start = "00:00"
        work_end = "00:00"
        has_start = False
        has_end = False
        
        for record in records:
            sort = record.get("sort")
            clock_time = record.get("clockTime", "")
            
            if clock_time and ":" in clock_time:
                time_formatted = clock_time[:5]
            else:
                time_formatted = clock_time
            
            if sort == 1:
                work_start = time_formatted
                has_start = True
            elif sort == 2:
                work_end = time_formatted
                has_end = True
        
        return work_start, work_end, has_start, has_end, None
        
    except requests.exceptions.RequestException as e:
        api_error = f"网络请求失败: {str(e)}"
        return "00:00", "00:00", False, False, api_error
    except Exception as e:
        api_error = f"数据解析失败: {str(e)}"
        return "00:00", "00:00", False, False, api_error

def generate_html(work_start, work_end, has_start, has_end, update_time, error_msg=None):
    """生成展示上下班时间的静态 HTML"""
    
    start_style = "" if has_start else "opacity: 0.6; background: #fef2f2;"
    end_style = "" if has_end else "opacity: 0.6; background: #fef2f2;"
    
    start_time_display = work_start if has_start else "未打卡"
    end_time_display = work_end if has_end else "未打卡"
    
    start_badge = "" if has_start else '<span style="font-size: 0.75rem; color: #ef4444; margin-left: 8px;">⚠️ 未打卡</span>'
    end_badge = "" if has_end else '<span style="font-size: 0.75rem; color: #ef4444; margin-left: 8px;">⚠️ 未打卡</span>'
    
    # 错误提示区域
    error_html = ""
    if error_msg:
        error_html = f'''
        <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 16px; padding: 1rem; margin: 1rem 0;">
            <div style="color: #dc2626; font-weight: 600; margin-bottom: 0.5rem;">⚠️ 获取打卡数据失败</div>
            <div style="color: #991b1b; font-size: 0.875rem;">{error_msg}</div>
            <div style="color: #6b7280; font-size: 0.75rem; margin-top: 0.5rem;">请检查网络或稍后重试，系统将自动在明天 9:00 重试</div>
        </div>
        '''
    
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
        
        {error_html}
        
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
        
        {f'<div class="warning">⚠️ 提示：今日打卡记录不完整，请及时打卡！</div>' if not error_msg and not (has_start and has_end) else ''}
        
        <div class="update-info">
            📅 数据更新时间：{update_time}<br>
            ⏰ 每日自动刷新<br>
            📊 状态：{'✅ 今日打卡完整' if (has_start and has_end) else ('❌ 数据获取失败' if error_msg else '⚠️ 打卡记录不完整')}
        </div>
    </div>
    <footer>
        Powered by GitHub Actions & Python
    </footer>
</body>
</html>"""
    return html_content

def main():
    # 创建 public 目录
    os.makedirs("public", exist_ok=True)
    
    # 获取上下班时间
    work_start, work_end, has_start, has_end, error_msg = fetch_work_schedule()
    
    # 生成时间戳（北京时间）
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz)
    beijing_time_str = beijing_time.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 生成 HTML
    html = generate_html(work_start, work_end, has_start, has_end, beijing_time_str, error_msg)
    
    # 写入 index.html
    index_path = "public/index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 保存 JSON 格式的数据（便于调试）
    json_data = {
        "update_time": beijing_time_str,
        "work_start": work_start,
        "work_end": work_end,
        "has_start": has_start,
        "has_end": has_end,
        "complete": has_start and has_end,
        "error": error_msg
    }
    with open("public/data.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
