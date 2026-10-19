# 销售数据智能查询 Agent

用中文提问，自动生成 SQL 查询本地销售数据，并展示图表。

## 功能

- 中文自然语言查询（如"TikTok上个月卖了多少钱"）
- 调用智谱 BigModel 生成 SQLite SQL
- 本地规则兜底，API 不可用时仍可响应常见查询
- 自动校正 LLM 对"品类/渠道"的字段混淆
- 前端展示：SQL 语句 + ECharts 图表 + 数据表格

## 项目文档

- [产品方案（一页纸）](docs/产品方案.md)：背景、目标用户、核心场景、架构与关键设计决策
- [需求文档（轻量版）](docs/需求文档.md)：功能清单 + 优先级 + 验收标准
- [测试记录](docs/测试记录.md)：15 问 LLM 路径 + 7 问断 Key 兜底实测，准确率与改进项
- [界面截图](docs/images)：[各渠道销售额对比](docs/images/界面-各渠道销售额对比.png) / [TikTok 上个月销售额](docs/images/界面-TikTok上个月销售额.png)

## 快速开始

```bash
# 1. 安装依赖
pip install flask openai python-dotenv

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的智谱 API Key
# 获取地址: https://open.bigmodel.cn/usercenter/apikeys

# 3. 导入数据
python 导入数据库.py

# 4. 启动服务
python agent.py

# 5. 浏览器访问
http://127.0.0.1:5000
```

## 项目结构

```
├── sales_data.csv       # 原始数据
├── sales.db             # SQLite 数据库（导入后生成）
├── 导入数据库.py         # CSV → SQLite 导入脚本
├── agent.py             # Flask Agent 服务（LLM + SQL 查询）
├── index.html           # 前端查询页面
├── .env                 # 环境变量（不上传）
├── .env.example         # 环境变量模板
└── .gitignore
```

## 数据说明

| 字段 | 说明 | 可选值 |
|------|------|--------|
| date | 日期 | 2026-01-01 ~ 2026-06-29 |
| channel | 销售渠道 | DTC, Amazon, TikTok, Store |
| category | 商品品类 | Blind Box, Plush, Action Figure, Accessories |
| traffic | 流量/访客数 | 整数 |
| orders | 订单数 | 整数 |
| sales | 销售额（元） | 浮点数 |
| cost | 成本（元） | 浮点数 |

## 示例查询

- TikTok上个月卖了多少钱
- 各渠道销售额对比
- 各品类销售额对比
- Blind Box 总销售额

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ZHIPU_API_KEY | 智谱 BigModel API Key | 必填 |
| ZHIPU_BASE_URL | API 地址 | https://open.bigmodel.cn/api/paas/v4/ |
| ZHIPU_MODEL | 模型名称 | glm-4-flash |

## 技术栈

- 后端：Flask + SQLite + OpenAI SDK（兼容智谱 API）
- 前端：原生 HTML + ECharts
- LLM：智谱 glm-4-flash
