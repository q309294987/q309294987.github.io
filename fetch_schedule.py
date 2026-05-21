# fetch_schedule.py
import json
import os
from datetime import datetime
import requests

# ---------- 配置 ----------
# 设置为 True 时使用 Mock 数据，False 时调用真实 API
USE_MOCK = True  # 测试时改为 True，正式使用时改为 False

# 真实 API 配置（当 USE_MOCK = False 时生效）
REAL_API_URL = "https://api.example.com/work-schedule"
REAL_API_KEY = os.environ.get("API_KEY", "")

# Mock 数据配置（当 USE_MOCK = True 时生效）
MOCK_CONFIG = {
    "work_start": "09:00",
    "work_end": "18:00",
    # 可以随机返回不同时间，模拟真实场景
    "enable_variation": True  # 是否让 mock 数据每天略微变化
}

def get_mock_schedule():
    """生成 mock 的上下班时间数据"""
    import random
    
    if MOCK_CONFIG.get("enable_variation", False):
        # 模拟每天不同的时间，范围上班 8:30-9:30，下班 17:30-19:00
        start_hour = random.randint(8, 9)
        start_minute = random.choice([0, 30])
        end_hour = random.randint(17, 19)
        end_minute = random.choice([0, 30])
        
        work_start = f"{start_hour:02d}:{start_minute:02d}"
        work_end = f"{end_hour:02d}:{end_minute:02d}"
        
        # 确保下班时间不早于上班时间
        if int(end_hour) < int(start_hour) or (int(end_hour) == int(start_hour) and end_minute <= start_minute):
            work_end = f"{int(start_hour)+8:02d}:{start_minute:02d}"
        
        return work_start, work_end
    else:
        # 使用固定 mock 数据
        return MOCK_CONFIG["work_start"], MOCK_CONFIG["work_end"]

def fetch_work_schedule():
    """
    调用外部 API 获取上班时间和下班时间。
    如果 USE_MOCK = True，则返回 mock 数据。
    """
    # 使用 Mock 数据
    if USE_MOCK:
        print("🔧 使用 Mock 数据模式")
        work_start, work_end = get_mock_schedule()
        print(f"📊 Mock 数据 - 上班: {work_start}, 下班: {work_end}")
        return work_start, work_end
    
    # 调用真实 API
    print("🌐 调用真实 API")
    headers = {}
    if REAL_API_KEY:
        headers["Authorization"] = f"Bearer {REAL_API_KEY}"
    
    try:
        response = requests.get(REAL_API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 根据你实际 API 返回的字段名调整
        work_start = data.get("work_start") or data.get("start_time") or data.get("上班时间", "09:00")
        work_end = data.get("work_end") or data.get("end_time") or data.get("下班时间", "18:00")
        
        print(f"✅ API 调用成功 - 上班: {work_start}, 下班: {work_end}")
        return work_start, work_end
    except Exception as e:
        print(f"❌ API 请求失败: {e}，使用默认时间")
        return "09:00", "18:00"

def generate_html(work_start, work_end, update_time, is_mock=False):
    """生成展示上下班时间的静态 HTML"""
    mock_badge = '<span style="background: #fbbf24; color: #78350f; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; margin-left: 10px;">🧪 测试模式</span>' if is_mock else ''
    
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
            background: #f5f7fb;
            color: #1e293b;
            text-align: center;
        }}
        .card {{
            background: white;
            border-radius: 32px;
            padding: 2rem;
            box-shadow: 0 20px 35px -10px rgba(0,0,0,0.1);
            margin-top: 10vh;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #0f172a;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
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
            min-width: 140px;
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
        }}
        .time {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 0.5rem;
            color: #0f172a;
        }}
        .update-info {{
            margin-top: 2rem;
            font-size: 0.8rem;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            padding-top: 1rem;
        }}
        .debug-info {{
            margin-top: 1rem;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 12px;
            font-size: 0.7rem;
            color: #475569;
            text-align: left;
            font-family: monospace;
        }}
        footer {{
            margin-top: 2rem;
            font-size: 0.75rem;
            color: #94a3b8;
        }}
        @media (max-width: 480px) {{
            .time-block {{ gap: 1rem; }}
            .time-item {{ padding: 0.8rem 1rem; min-width: 110px; }}
            .time {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>
            🏢 今日工作时间
            {mock_badge}
        </h1>
        <div class="time-block">
            <div class="time-item">
                <div class="label">⏰ 上班时间</div>
                <div class="time">{work_start}</div>
            </div>
            <div class="time-item">
                <div class="label">🏠 下班时间</div>
                <div class="time">{work_end}</div>
            </div>
        </div>
        <div class="update-info">
            📅 数据更新时间：{update_time}<br>
            ⏰ 每日自动刷新（北京时间 9:00）<br>
            🔄 下次更新：明天上午 9:00
        </div>
        <div class="debug-info">
            🔍 调试信息：<br>
            - 数据来源：{'Mock 数据（测试模式）' if is_mock else '外部 API'}<br>
            - 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            - GitHub Actions 状态：✅ 正常运行
        </div>
    </div>
    <footer>
        Powered by GitHub Actions & Python | 自动部署测试版本
    </footer>
</body>
</html>"""
    return html_content

def main():
    # 打印环境信息，便于调试
    print("=" * 50)
    print("🚀 开始生成静态页面")
    print(f"📁 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python 版本: {__import__('sys').version}")
    print(f"⚙️  使用 Mock 模式: {USE_MOCK}")
    print("=" * 50)
    
    # 获取上下班时间
    work_start, work_end = fetch_work_schedule()
    
    # 生成时间戳（使用 UTC 时间转为北京时间展示）
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    beijing_time = datetime.now(beijing_tz)
    beijing_time_str = beijing_time.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 生成 HTML
    html = generate_html(work_start, work_end, beijing_time_str, is_mock=USE_MOCK)
    
    # 创建 public 目录（GitHub Pages 默认从该目录发布）
    os.makedirs("public", exist_ok=True)
    
    # 写入 index.html
    index_path = "public/index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 额外生成一个 version.json 文件，方便查看部署状态
    version_info = {
        "version": datetime.now().isoformat(),
        "work_start": work_start,
        "work_end": work_end,
        "is_mock": USE_MOCK,
        "update_time": beijing_time_str
    }
    with open("public/version.json", "w", encoding="utf-8") as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print("✅ 成功生成以下文件：")
    print(f"   - {index_path}")
    print(f"   - public/version.json")
    print(f"📊 上下班时间: {work_start} - {work_end}")
    print("=" * 50)
    
    # 验证文件是否真的创建成功
    if os.path.exists(index_path):
        file_size = os.path.getsize(index_path)
        print(f"✅ 文件验证成功，大小: {file_size} bytes")
    else:
        print("❌ 文件创建失败！")
        exit(1)

if __name__ == "__main__":
    main()
