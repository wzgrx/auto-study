# 平台分析报告：宁夏继续教育 & 华医网

## 一、宁夏继续教育 (gp.chinahrt.com)

### 已存在资源

| 资源 | 链接 | 说明 |
|------|------|------|
| GitHub 项目 | yikuaibaiban/chinahrt-autoplay ⭐42 | JS 源码，Apache-2.0，可直接读代码 |
| 油猴脚本 | 400775，5万安装 | 全自动刷课，26KB |
| 使用文档 | yikuaibaiban.github.io/chinahrt-autoplay-docs | 教程完整 |
| CSDN 分析文 | 多篇 | 详细解析了技术原理 |
| ScriptCat 脚本 | 包头/赤峰/宁夏/梅河口/桦甸专区 | 各地区的适配 |

### 技术要点

| 特性 | 说明 |
|------|------|
| 框架 | **Vue SPA**，hash 路由 (`#/v_selected_course`, `#/v_video`) |
| 视频 | 跨域 iframe (`videoadmin.chinahrt.com`) |
| 登录 | 有图形验证码（ddddocr 可处理） |
| 反检测 | 鼠标离开暂停、playbackRate 检测 |
| 播放模式 | 正常 / 三段式(每段播90s) / 秒播(首尾各1秒) |
| 多区域 | 宁夏/包头/赤峰/梅河口等共用 chinahrt 系统 |
| 弹窗 | 继续播放/确定弹窗 |

### 可复用的 JS 代码片段

从 `yikuaibaiban/chinahrt-autoplay` 项目可以提取：

- 视频自动播放逻辑
- 失去焦点防暂停
- 播放速度控制
- 视频拖动开启
- 播放列表管理
- 各区域差异化配置

---

## 二、华医网 (91huayi.com)

### 已存在资源

| 资源 | 链接 | 说明 |
|------|------|------|
| 油猴脚本 | 441391「华医网-帮帮客网课助手」2.5万安装 | 支持华医网/好医生等 |
| 油猴脚本 | 3054「华医网小助手」 | 含考试助手 |
| 技术分析 | plxzjd.com 华医网跳过视频学习 | 服务器计时分析 |

### 技术要点

| 特性 | 说明 |
|------|------|
| 登录 | 账号密码，部分有图形验证码 |
| 视频 | **服务器端计时** — 必须真实观看，不能快进绕过 |
| 课程结构 | 32个课件（12公共+20专业），需完成≥60%才能考试 |
| 考试 | 模拟考（人脸识别建档）→ 正式考（APP端 only） |
| 多子平台 | 91huayi.com, yxlearning.com, cmechina.net, ghlearning.com 等 |
| 学习卡 | 需要购买学习卡充值 |
| 查学分 | 有独立的学分查询入口 |

### 关键发现：服务器计时

```
华医网对课程学习时长的监测是单课程的
→ 不能靠快进/跳转骗过系统
→ 必须真实挂够时长
→ 但可以同时开多个课程并行计时
```

这意味着我们的播放策略需要调整：
- 对于华医网：**正常速度播放，不修改 playbackRate**
- 利用多标签页并行播放多个课程

---

## 三、对架构的补充修改

### 新增：播放模式配置

```python
# config.py 新增
PLAY_MODE = {
    "chinahrt": {                         # 宁夏继续教育
        "speed": 1.0,                     # 不修改playbackRate（防检测）
        "segment_mode": "三段",            # 正常/三段(90s)/秒播
        "segment_duration": 90,           # 三段模式每段播秒数
        "allow_drag": True,               # 允许拖动进度条
        "prevent_mouse_leave": True,      # 防鼠标离开暂停
    },
    "huayiwang": {                        # 华医网
        "speed": 1.0,                     # 必须原速（服务器计时）
        "segment_mode": "正常",            # 只能正常播放
        "min_watch_seconds": 600,         # 最少观看10分钟（防秒过）
        "parallel_tabs": True,            # 允许多标签页并行
    }
}
```

### 新增：chinahrt 插件选择器（基于现有经验）

```python
class ChinahrtPlugin(SitePlugin):
    name = "chinahrt"
    domains = ["gp.chinahrt.com", "chinahrt.com"]
    
    # 已知路由
    ROUTES = {
        'login': '#/commonLogin',
        'course_list': '#/v_selected_course',
        'course_detail': '#/v_courseDetails',
        'video': '#/v_video',
    }
    
    # 已知选择器
    login_selectors = {
        'username': 'input[type="text"]',
        'password': 'input[type="password"]', 
        'captcha_img': 'img[src*="captcha"]',
        'captcha_input': 'input[name="captcha"]',
        'submit': 'button[type="submit"]',
    }
    
    # 已知 JS 操作
    VIDEO_PLAY_JS = """
        var v = document.querySelector('video') 
            || document.querySelector('iframe')?.contentDocument?.querySelector('video');
        if(v) { v.muted = true; v.play(); }
    """
    
    ANTI_PAUSE_JS = """
        // 防鼠标离开暂停
        document.addEventListener('visibilitychange', function(e){e.stopPropagation()}, true);
        // 防焦点丢失暂停
        window.addEventListener('blur', function(e){e.stopPropagation()}, true);
    """
```

### 新增：华医网插件骨架

```python
class HuayiPlugin(SitePlugin):
    name = "huayiwang"
    domains = ["91huayi.com", "yxlearning.com", "cmechina.net"]
    
    # 子平台差异配置
    SUB_PLATFORMS = {
        '91huayi.com': {'login_type': 'account', 'has_captcha': False},
        'yxlearning.com': {'login_type': 'account', 'has_captcha': True},
        'cmechina.net': {'login_type': 'account', 'has_captcha': False},
    }
    
    # 注意：服务器计时，不能快进
    WATCH_STRATEGY = "normal_speed"  # 必须原速
```

### 新增：并行播放模块（华医网用）

```python
class ParallelPlayer:
    """并行播放器 — 华医网需要同时挂多个课程"""
    
    def play_multiple(self, courses: list, max_parallel: int = 3):
        """同时播放多个课程
        
        利用多个标签页同时挂机
        每个标签页各播一个课程
        服务器独立计时，互不影响
        """
        tabs = brain.get_all_tabs()
        for i, course in enumerate(courses[:max_parallel]):
            tab = tabs[i]
            # 每个标签页导航到一个课程
            # 开始播放
            # 各自独立监控进度
```

---

## 四、总结

| 维度 | chinahrt | 华医网 |
|------|----------|--------|
| 技术难度 | ⭐⭐ 已有经验 | ⭐⭐⭐ 服务器计时 |
| 关键难点 | iframe跨域、防快进检测 | 必须真实观看、人脸识别考试 |
| 播放策略 | 可秒播(首尾各1s) | 必须原速(服务器计时) |
| 考试 | 无（自动完成） | 模拟考+正式考(APP only) |
| 可复用代码 | yikuaibaiban 42⭐项目 | 帮帮客油猴脚本 2.5万安装 |
| 建议优先级 | 先做chinahrt（经验丰富） | 再做华医网（服务器计时机制需探索） |

**先做 chinahrt 再做华医网。**
