# 全能刷课平台 / Auto-Study

> 基于 DrissionPage + DeepSeek + Gemma 4 的通用刷课框架。
> 支持宁夏继续教育(gp.chinahrt.com)、华医网(91huayi.com) 等平台。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置账号
cp .env.example .env
# 编辑 .env 填入账号密码

# 3. 确保 Edge 浏览器已开启 CDP 端口 9223

# 4. 运行
python3 launcher.py chinahrt --auto
```

## 项目结构

```
auto-study/
├── core/                      # 17 个核心模块
│   ├── 01_config.py
│   ├── 02_logger.py
│   ├── ...
│   └── 17_scheduler.py
├── plugins/                   # 站点插件
├── data/                      # 持久化数据
├── logs/                      # 日志
├── AGENTS.md                  # AI 助手开发指南（每次动代码前先读）
├── ARCHITECTURE.md            # 架构设计
├── PLATFORM_ANALYSIS.md       # 平台分析
└── README.md
```

## 开发指引

**如果你是 AI 助手，动代码之前先读 `AGENTS.md`。**
