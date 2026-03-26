#!/usr/bin/env python3
"""
上传 Horizon 报告到飞书文档
使用飞书自建应用 API
"""
import os
import sys
import requests
import json
from datetime import datetime

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

def grant_permission(token, doc_token, owner_open_id):
    """授予用户编辑权限"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/permissions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "member_type": "openid",
        "member_id": owner_open_id,
        "perm": "full_access"
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        return data.get('code') == 0
    except Exception as e:
        print(f"Grant permission warning: {e}")
        return False

def write_content_blocks(token, doc_token, content):
    """写入文档内容（分批写入）"""
    # 获取文档块
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    if data.get('code') != 0:
        print(f"Get blocks failed: {data}")
        return False
    
    items = data.get('data', {}).get('items', [])
    if not items:
        print("No blocks found")
        return False
    
    # 找到第一个 page 块
    page_block = None
    for item in items:
        if item.get('block_type') == 1:  # page
            page_block = item
            break
    
    if not page_block:
        print("Page block not found")
        return False
    
    block_id = page_block.get('block_id')
    
    # 将内容分段（飞书限制每段 5000 字符）
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
    
    # 分批写入
    for i, chunk in enumerate(chunks):
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{block_id}/children"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "children": [
                {
                    "block_type": 2,  # text
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": chunk
                                }
                            }
                        ]
                    }
                }
            ]
        }
        resp = requests.post(url, headers=headers, json=payload)
        if resp.json().get('code') != 0:
            print(f"Write chunk {i} failed: {resp.json()}")
            return False
    
    return True

def main():
    # 从环境变量读取配置
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    report_file = os.environ.get('REPORT_FILE', 'output/horizon-daily.md')
    doc_title = os.environ.get('DOC_TITLE', f'Horizon Daily - {datetime.now().strftime("%Y-%m-%d")}')
    owner_open_id = os.environ.get('OWNER_OPEN_ID', 'ou_f80617e98f143959124726775f8ae7d7')
    
    if not app_id or not app_secret:
        print("FEISHU_APP_ID and FEISHU_APP_SECRET required")
        sys.exit(1)
    
    # 读取报告
    if not os.path.exists(report_file):
        print(f"Report file not found: {report_file}")
        # 尝试查找任何 .md 文件
        import glob
        md_files = glob.glob("output/*.md")
        if md_files:
            report_file = md_files[0]
            print(f"Using found report: {report_file}")
        else:
            sys.exit(1)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Report length: {len(content)} chars")
    
    # 获取 token
    token = get_feishu_token(app_id, app_secret)
    if not token:
        sys.exit(1)
    
    # 创建文档
    doc_token = create_document(token, doc_title)
    if not doc_token:
        sys.exit(1)
    
    print(f"Created doc: https://feishu.cn/docx/{doc_token}")
    
    # 授予权限
    if grant_permission(token, doc_token, owner_open_id):
        print(f"Granted permission to {owner_open_id}")
    
    # 写入内容
    if write_content_blocks(token, doc_token, content):
        print(f"Content written successfully")
        
        # 输出供 GitHub Actions 使用
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write(f"doc_token={doc_token}\n")
            f.write(f"doc_url=https://feishu.cn/docx/{doc_token}\n")
        
        print(f"\n✅ Document uploaded: https://feishu.cn/docx/{doc_token}")
    else:
        print("Failed to write content")
        sys.exit(1)

if __name__ == '__main__':
    main()
