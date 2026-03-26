#!/usr/bin/env python3
"""
将报告内容合并到同一个飞书文档
每天创建新文档，两个工作流分别追加不同章节
"""
import os
import sys
import requests
import json
from datetime import datetime

# 文档状态文件（用于在同一天内共享文档 token）
STATE_FILE = "/tmp/feishu_doc_state.json"

def get_feishu_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        print(f"Auth failed: {data}")
        return None
    return data.get('tenant_access_token')

def create_document(token, title):
    """创建飞书文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title}
    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()
    if data.get('code') != 0:
        print(f"Create doc failed: {data}")
        return None
    return data.get('data', {}).get('document', {}).get('document_id')

def get_doc_blocks(token, doc_token):
    """获取文档块列表"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get('code') != 0:
        return None
    return data.get('data', {}).get('items', [])

def append_content(token, doc_token, parent_block_id, content, heading=None):
    """追加内容到文档"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{parent_block_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    children = []
    
    # 如果有标题，先添加标题
    if heading:
        children.append({
            "block_type": 4,  # heading2
            "heading2": {
                "elements": [{"text_run": {"content": heading}}]
            }
        })
    
    # 分段添加内容
    chunks = []
    lines = content.split('\n')
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) > 4500:
            chunks.append(current_chunk)
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk)
    
    for chunk in chunks:
        children.append({
            "block_type": 2,  # text
            "text": {
                "elements": [{"text_run": {"content": chunk}}]
            }
        })
    
    payload = {"children": children}
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json().get('code') == 0

def load_state():
    """加载状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def main():
    if len(sys.argv) < 3:
        print("Usage: merge_to_feishu.py <report_file> <section_type>")
        print("section_type: 'github' or 'tech'")
        sys.exit(1)
    
    report_file = sys.argv[1]
    section_type = sys.argv[2]  # 'github' or 'tech'
    
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    owner_open_id = os.environ.get('OWNER_OPEN_ID', 'ou_f80617e98f143959124726775f8ae7d7')
    
    if not app_id or not app_secret:
        print("FEISHU_APP_ID and FEISHU_APP_SECRET required")
        sys.exit(1)
    
    if not os.path.exists(report_file):
        print(f"Report file not found: {report_file}")
        sys.exit(1)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    today = datetime.now().strftime('%Y-%m-%d')
    state = load_state()
    
    # 获取 token
    token = get_feishu_token(app_id, app_secret)
    if not token:
        sys.exit(1)
    
    # 检查是否已有今天的文档
    doc_token = state.get(today)
    
    if not doc_token:
        # 创建新文档
        doc_title = f"Horizon 科技日报 - {today}"
        doc_token = create_document(token, doc_title)
        if not doc_token:
            sys.exit(1)
        
        state[today] = doc_token
        save_state(state)
        
        print(f"Created new doc: https://feishu.cn/docx/{doc_token}")
        
        # 添加文档标题和简介
        blocks = get_doc_blocks(token, doc_token)
        if blocks:
            page_block = None
            for block in blocks:
                if block.get('block_type') == 1:
                    page_block = block
                    break
            
            if page_block:
                intro = f"""# Horizon 科技日报 - {today}

> 本日报分为两部分：
> 1. 🔥 GitHub 热点项目
> 2. 🏢 科技巨头动态

---

"""
                append_content(token, doc_token, page_block.get('block_id'), intro)
    else:
        print(f"Using existing doc: https://feishu.cn/docx/{doc_token}")
    
    # 获取页面块
    blocks = get_doc_blocks(token, doc_token)
    if not blocks:
        print("Failed to get doc blocks")
        sys.exit(1)
    
    page_block = None
    for block in blocks:
        if block.get('block_type') == 1:
            page_block = block
            break
    
    if not page_block:
        print("Page block not found")
        sys.exit(1)
    
    # 根据类型添加不同章节
    if section_type == 'github':
        heading = "🔥 GitHub 热点项目"
        # 提取报告中的条目
        items = extract_items(content)
        formatted = format_items(items, "github")
        append_content(token, doc_token, page_block.get('block_id'), formatted, heading)
        print("Added GitHub section")
        
    elif section_type == 'tech':
        heading = "🏢 科技巨头动态"
        items = extract_items(content)
        formatted = format_items(items, "tech")
        append_content(token, doc_token, page_block.get('block_id'), formatted, heading)
        print("Added Tech Giants section")
    
    # 输出文档链接
    doc_url = f"https://feishu.cn/docx/{doc_token}"
    print(f"\n✅ Document: {doc_url}")
    
    # 设置 GitHub Actions 输出
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f"doc_token={doc_token}\n")
        f.write(f"doc_url={doc_url}\n")

def extract_items(content):
    """提取报告中的条目"""
    items = []
    # 简单提取标题和链接
    import re
    
    # 匹配条目
    pattern = r'## \[(.+?)\]\((.+?)\)\s+⭐️\s+([\d.]+)/10\s*\n\n(.+?)(?:\n\n---|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        items.append({
            'title': match[0],
            'url': match[1],
            'score': match[2],
            'summary': match[3].strip()
        })
    
    return items

def format_items(items, section_type):
    """格式化条目为中文"""
    if not items:
        return "暂无内容\n"
    
    result = f"\n> 共 {len(items)} 条精选内容\n\n"
    
    for i, item in enumerate(items, 1):
        result += f"""### {i}. {item['title']}

**评分**: ⭐️ {item['score']}/10

**原文链接**: [{item['url']}]({item['url']})

{item['summary']}

---

"""
    
    return result

if __name__ == '__main__':
    main()
