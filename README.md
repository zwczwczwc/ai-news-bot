# Horizon GitHub Actions 部署方案

## 概述

使用 GitHub Actions 全自动运行 Horizon AI 新闻聚合器，**你的服务器零负担**。

## 架构

```
GitHub Actions (云端运行)
├── 定时触发 (每天 8:00 北京时间)
├── 抓取多源新闻 (RSS/GitHub/Reddit)
├── AI 评分 (Gemini Flash - 轻量快速)
├── 生成中文日报
├── 发送飞书通知
└── 部署到 GitHub Pages

你的服务器: 仅接收飞书消息，零计算负担
```

## 内存优化配置

针对你的服务器内存限制，已做以下优化：

| 优化项 | 原始配置 | 优化后 |
|--------|----------|--------|
| AI 模型 | GPT-4/Claude | Gemini Flash (更快更省) |
| 并发数 | 10 | 3 |
| Web 搜索 | 开启 | 关闭 |
| 社区评论 | 开启 | 关闭 |
| 数据源 | 全部 | 精选 RSS + GitHub |
| 输出条目 | 50 | 20 |

## 快速开始

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub 创建新仓库，例如: ai-news-bot
# 然后上传本目录的文件
```

### 2. 配置 GitHub Secrets

在仓库 Settings → Secrets → Actions 中添加：

| Secret 名称 | 说明 | 获取方式 |
|-------------|------|----------|
| `GEMINI_API_KEY` | Gemini API Key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `FEISHU_WEBHOOK` | 飞书机器人 webhook | 飞书群设置 → 添加机器人 |
| `OPENAI_API_KEY` | (可选) OpenAI Key | OpenAI 控制台 |
| `ANTHROPIC_API_KEY` | (可选) Claude Key | Anthropic 控制台 |

### 3. 手动触发测试

```bash
# 进入 Actions 标签页
# 选择 "Daily AI News - Horizon"
# 点击 "Run workflow"
```

### 4. 查看结果

- **飞书**: 收到日报消息
- **GitHub Pages**: `https://你的用户名.github.io/ai-news-bot/daily/`
- **Artifacts**: Actions 页面下载原始文件

## 定时任务

默认配置：
- **时间**: 每天北京时间 8:00
- **时区**: Asia/Shanghai
- **免费额度**: 每月 2000 分钟 (完全够用)

## 自定义配置

编辑 `.github/workflows/daily-news.yml` 中的 `config.json` 部分：

```json
{
  "sources": {
    "rss": [
      "添加你自己的 RSS 源"
    ]
  },
  "ai": {
    "provider": "gemini",  // 或 "openai", "anthropic"
    "score_threshold": 6.0  // 评分阈值 (0-10)
  }
}
```

## 文件说明

```
.
├── .github/
│   └── workflows/
│       └── daily-news.yml    # Actions 工作流
├── README.md                  # 本文件
└── .gitignore                 # Git 忽略文件
```

## 故障排查

### 问题: Actions 运行失败

**检查点**:
1. Secrets 是否正确配置
2. API Key 是否有效
3. 飞书 webhook 是否正确

**查看日志**:
- Actions 页面 → 点击失败的运行 → 查看日志

### 问题: 飞书未收到消息

**检查**:
1. `FEISHU_WEBHOOK` 是否配置
2. 飞书机器人是否有发送权限
3. 消息内容是否超长 (已做截断处理)

### 问题: 内存不足 (Actions 中)

**解决**: 已优化配置，如仍有问题：
1. 减少 `max_items` 到 10
2. 减少 RSS 源数量
3. 关闭更多功能

## 费用说明

| 项目 | 费用 |
|------|------|
| GitHub Actions | 免费 (2000 分钟/月) |
| Gemini API | 免费额度充足 |
| GitHub Pages | 免费 |
| **总计** | **完全免费** |

## 进阶配置

### 添加更多数据源

在 workflow 文件中编辑 `config.json`:

```json
{
  "sources": {
    "rss": [
      "https://news.ycombinator.com/rss",
      "https://www.reddit.com/r/MachineLearning/.rss",
      "https://blog.google/technology/ai/rss/",
      "https://openai.com/blog/rss.xml",
      "https://www.anthropic.com/rss.xml"
    ]
  }
}
```

### 修改发送时间

编辑 workflow 文件:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'    # 每天 UTC 0:00 (北京时间 8:00)
    - cron: '0 12 * * *'   # 再加 UTC 12:00 (北京时间 20:00)
```

### 使用自己的 Horizon Fork

```yaml
# 修改克隆地址
- name: Clone Horizon
  run: |
    git clone https://github.com/你的用户名/Horizon.git /tmp/horizon
```

## 相关链接

- [Horizon 官方仓库](https://github.com/Thysrael/Horizon)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [Gemini API 文档](https://ai.google.dev/)
