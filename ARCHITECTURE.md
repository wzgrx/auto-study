# 全能刷课平台 — 架构设计 v5（最终版）

## 目标平台

| 平台 | 域名 | 优先级 |
|------|------|--------|
| 宁夏继续教育 | gp.chinahrt.com | ✅ 现刷 |
| 华医网 | huayiwang.com | ✅ 现刷 |
| 未来扩展 | 超星/智慧树/职教云/... | 📌 插件化 |

## 技术选型

```
底层浏览器:  DrissionPage → Edge (CDP 9223)
推理大脑:    DeepSeek V4 (API)
视觉识别:    Gemma 4 12B (llama-server:8080)
验证码OCR:  ddddocr
数据库:     SQLite (轻量持久化)
```

---

## 最终 18 个模块（按构建顺序编号）

```
 1  config.py       配置管理
 2  tab_manager.py  标签页管理器 🔥新增
 3  logger.py       日志系统
 4  exceptions.py   异常+重试
 5  brain.py        基础能力层（核心大脑）
 6  anti_detect.py  反检测层
 7  persistence.py  持久化层
 8  captcha.py      验证码处理
 9  login.py        万能登录层
10  scanner.py      课程识别层
11  player.py       视频播放层
12  quiz.py         答题模块
13  notifier.py     通知模块
14  health.py       健康监控
15  plugin.py       站点插件体系
16  progress.py     进度管理层
17  reporter.py     报告层
18  scheduler.py    调度引擎
```

编号按**构建顺序**排列：从底层到上层，先写基础能力再写业务。

| 编号 | 模块 | 一句话 | 先写原因 |
|------|------|--------|---------|
| **1** | config.py | 所有配置集中管理 | 其他模块都依赖它 |
| **2** | tab_manager.py | 3固定标签页管理 | 连接浏览器的基础 |
| **3** | logger.py | 统一日志 | 写代码时就要日志 |
| **4** | exceptions.py | 异常分类+重试装饰器 | 错误处理的基础 |
| **5** | brain.py | 核心大脑，所有操作的基础 | 所有业务模块都依赖它 |
| **6** | anti_detect.py | 防检测措施 | 不依赖其他业务模块 |
| **7** | persistence.py | 持久化 | 不依赖其他业务模块 |
| **8** | captcha.py | 验证码处理 | 独立 |
| **9** | login.py | 万能登录 | 依赖 brain |
| **10** | scanner.py | 课程识别 | 依赖 brain |
| **11** | player.py | 视频播放 | 依赖 brain + anti_detect |
| **12** | quiz.py | 自动答题 | 依赖 brain |
| **13** | notifier.py | 通知推送 | 独立 |
| **14** | health.py | 健康监控 | 独立 |
| **15** | plugin.py | 站点插件体系 | 依赖 brain |
| **16** | progress.py | 进度管理 | 独立 |
| **17** | reporter.py | 报告输出 | 独立 |
| **18** | scheduler.py | 调度引擎 | 依赖上面所有 |

---

## S1 — config.py 配置管理（新增支撑模块）

```python
class Config:
    """统一配置 — 环境变量 + 配置文件 + 默认值"""
    
    # 浏览器
    CDP_PORT: int = 9223
    CDP_HOST: str = "localhost"
    
    # 凭据（只从环境变量/加密文件读取，永不硬编码）
    ACCOUNTS: dict = {}  # {"chinahrt": {"user":"xxx","pass":"yyy"}, ...}
    
    # LLM
    DEEPSEEK_API_KEY: str
    DEEPSEEK_MODEL: str = "deepseek-chat"
    GEMMA_URL: str = "http://localhost:8080/v1"
    
    # 运行参数
    MAX_HOURS: float = 24        # 最大运行时长
    MAX_RETRIES: int = 3         # 失败重试次数
    RETRY_DELAY: int = 30        # 重试间隔秒
    COURSE_COOLDOWN: int = 60    # 课程间冷却秒
    HUMAN_DELAY: tuple = (1, 3)  # 操作间随机延迟(秒)
    
    # 视频
    PLAY_SPEED: float = 1.0      # 播放倍速（不解playbackRate，仅计时参考）
    MIN_WATCH_SEC: int = 300     # 最少观看秒数，防秒过
    PROGRESS_POLL_SEC: int = 30  # 进度查询间隔
    
    # 答题
    QUIZ_ENABLED: bool = True
    QUIZ_CORRECT_RATE: float = 0.85  # 正确率（随机错题防检测）
    QUIZ_DB_PATH: str = "data/quiz_cache.db"
    
    # 报告
    FEISHU_WEBHOOK: str = ""
    
    @classmethod
    def load(cls):
        """从环境变量 + ~/.hermes/.env + 配置文件加载"""
```

## S2 — logger.py 日志系统（新增支撑模块）

```python
import logging, sys
from pathlib import Path

def setup_logger(name: str = "auto-study") -> logging.Logger:
    """统一日志配置
    
    - 控制台输出: INFO 级别
    - 文件日志: DEBUG 级别（按日期轮转，5MB，保留7天）
    - 格式: [时间] [模块] [级别] 消息
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 控制台 Handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(name)s] %(message)s', datefmt='%H:%M:%S'))
    
    # 文件 Handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_dir / "run.log", maxBytes=5*1024*1024, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
```

## S3 — exceptions.py 异常体系 + 重试（新增支撑模块）

```python
class AutoStudyError(Exception):      # 所有异常基类
class LoginError(AutoStudyError):      # 登录失败
class CaptchaError(LoginError):        # 验证码识别失败
class CourseScanError(AutoStudyError): # 课程识别失败
class VideoError(AutoStudyError):      # 视频播放异常
class QuizError(AutoStudyError):       # 答题异常
class TimeoutError(AutoStudyError):    # 操作超时
class HumanIntervention(  AutoStudyError):  # 需要人工介入

# 重试装饰器
def retry(max_attempts=3, delay=30, on_exception=None):
    """失败自动重试，隔30秒再试，3次还失败就跳过"""
```

---

## 1️⃣ brain.py — 基础能力层（核心大脑）

```python
class BrowserBrain:
    """浏览器大脑 — 封装所有基础操作
    
    整个系统的基石，所有上层模块只通过这个类操作浏览器。
    """
    
    def __init__(self):
        from DrissionPage import Chromium
        self.browser = Chromium(addr=Config.CDP_PORT)
        self.logger = logging.getLogger("brain")
    
    # ── 标签页管理 ──
    def get_tab(self, index: int = 0):
        """获取指定标签页（0/1/2 对应 3个固定标签页）"""
        return self.browser.get_tab(index)
    
    def get_all_tabs(self):
        return [self.browser.get_tab(i) for i in range(3)]
    
    # ── 阅读页面 ──
    def read_text(self, tab) -> str:
        """读取页面全部文本"""
        return tab.ele('tag:body').text
    
    def read_title(self, tab) -> str:
        return tab.title
    
    def read_url(self, tab) -> str:
        return tab.url
    
    def read_hash(self, tab) -> str:
        """SPA 路由 hash"""
        return tab.run_js('return location.hash')
    
    # ── 视觉分析（Gemma 4）──
    def analyze_screenshot(self, tab, question: str) -> str:
        """截图 → Gemma 4 分析 → 返回文字理解
        
        核心方法：用视觉识别页面布局、按钮位置、验证码等
        """
        path = tab.get_screenshot()  # DrissionPage 自带截图
        return self._ask_gemma(path, question)
    
    def _ask_gemma(self, image_path: str, question: str) -> str:
        """调 llama-server API"""
        import base64, httpx
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = httpx.post(
            f'{Config.GEMMA_URL}/chat/completions',
            json={
                'model': 'gemma-4-12b',
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                        {'type': 'text', 'text': question}
                    ]
                }],
                'max_tokens': 2048,
            },
            timeout=30
        )
        return resp.json()['choices'][0]['message']['content']
    
    # ── 页面操作 ──
    def click(self, tab, selector_or_el, timeout=10):
        """点击（自带等待和重试）"""
        if isinstance(selector_or_el, str):
            el = tab.ele(selector_or_el, timeout=timeout)
        else:
            el = selector_or_el
        el.click()
        time.sleep(random.uniform(*Config.HUMAN_DELAY))
    
    def input_text(self, tab, selector, text: str):
        """输入文字（模拟真人打字节奏）"""
        el = tab.ele(selector)
        el.clear()
        for char in text:
            el.input(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def navigate(self, tab, url: str):
        """导航并等待加载"""
        tab.get(url)
        time.sleep(2)
    
    def navigate_hash(self, tab, hash_str: str):
        """SPA hash 导航"""
        if not hash_str.startswith('#'):
            hash_str = '#' + hash_str
        tab.run_js(f"location.hash='{hash_str}'")
        time.sleep(3)
    
    def execute_js(self, tab, js: str):
        """执行 JS 并返回值"""
        return tab.run_js(js)
```

## 2️⃣ login.py — 万能登录层

```python
class UniversalLogin:
    """万能登录器 — 适配 chinahrt / 华医网 / 未来所有站点"""
    
    def __init__(self, brain: BrowserBrain):
        self.brain = brain
        self.logger = logging.getLogger("login")
    
    @retry(max_attempts=3, delay=30)
    def login(self, site: str, url: str, username: str, password: str) -> bool:
        """登录任意网站
        
        流程:
        1. 导航到登录页
        2. 截图 → Gemma 4 分析页面的登录表单结构
        3. DeepSeek 决定如何填表
        4. 填账号密码
        5. 验证码处理（ddddocr / Gemma / 人工）
        6. 点登录
        7. 验证是否成功
        """
        tab = self.brain.get_tab(0)
        self.brain.navigate(tab, url)
        time.sleep(3)
        
        # 方案A: 站点插件有已知选择器 → 直接用
        plugin = PluginRegistry.get(site)
        if plugin and plugin.login_selectors:
            return self._login_with_selectors(tab, username, password, plugin)
        
        # 方案B: 未知站点 → AI 分析页面
        return self._login_with_vision(tab, username, password)
    
    def _login_with_selectors(self, tab, username, password, plugin):
        """有已知选择器 → 直接填"""
        self.brain.input_text(tab, plugin.login_selectors['username'], username)
        self.brain.input_text(tab, plugin.login_selectors['password'], password)
        self._handle_captcha(tab, plugin)
        self.brain.click(tab, plugin.login_selectors['submit'])
        return self._verify(tab)
    
    def _login_with_vision(self, tab, username, password):
        """未知站点 → Gemma 分析页面"""
        analysis = self.brain.analyze_screenshot(
            tab, "描述这个登录页面的布局：用户名输入框、密码输入框、验证码、登录按钮分别在哪里？")
        # DeepSeek 解析分析结果，决定操作步骤
        actions = self._ask_deepseek(f"根据页面分析: {analysis}\n决定如何填 {username}/{password}")
        # 执行操作...
        return self._verify(tab)
    
    def _handle_captcha(self, tab, plugin=None):
        """验证码处理三连"""
        # 1. ddddocr 自动识别
        # 2. Gemma 4 看图识别（复杂验证码）
        # 3. 都不行 → 通知用户手动输入
        pass
    
    def _verify(self, tab) -> bool:
        """验证登录是否成功"""
        text = self.brain.read_text(tab)
        return not any(kw in text for kw in ['登录', 'login', '密码错误'])
```

## 3️⃣ scanner.py — 课程识别层

```python
class CourseScanner:
    """识别哪些课程需要刷"""
    
    def __init__(self, brain: BrowserBrain):
        self.brain = brain
    
    def scan(self, tab) -> list[Course]:
        """扫描页面上的课程
        
        返回: [Course(id, name, progress, url, type)]
        """
        # 1. 读页面文本
        text = self.brain.read_text(tab)
        
        # 2. 截图分析
        vision = self.brain.analyze_screenshot(tab, "列出所有课程及其进度")
        
        # 3. DeepSeek 综合判断
        result = self._ask_deepseek(
            f"页面文本: {text}\n视觉分析: {vision}\n"
            f"请输出所有未完成课程（进度<100%），格式: 课程名 | 进度% | 类型")
        
        return self._parse_courses(result)
    
    def find_entry(self, tab, course) -> str:
        """找到进入课程学习的入口"""
        # 用 Gemma 截图分析哪里可以点进去
        return self.brain.analyze_screenshot(tab, f"要进入课程'{course.name}'，应该点击哪里？")
```

## 4️⃣ player.py — 视频播放层

```python
class VideoPlayer:
    """全自动视频播放"""
    
    def __init__(self, brain: BrowserBrain):
        self.brain = brain
        self.logger = logging.getLogger("player")
    
    @retry(max_attempts=3, delay=60)
    def play(self, tab, course: Course) -> bool:
        """播放课程视频直到完成"""
        
        # 1. 注入反检测JS
        AntiDetect.inject(tab)
        
        # 2. 检测视频元素
        video_info = self._detect_video(tab)
        if not video_info:
            self.logger.warning(f"{course.name}: 未找到视频")
            return False
        
        # 3. 获取时长
        duration = float(video_info['duration'])
        if duration < 60:
            self.logger.info(f"{course.name}: 短视频({duration}s)，直接等待")
            time.sleep(duration + 5)
            return True
        
        # 4. 静音播放
        self._play_video(tab, video_info)
        
        # 5. 监控进度
        start_time = time.time()
        last_progress = 0
        stall_count = 0
        
        while True:
            # 检查运行时长
            if time.time() - start_time > Config.MAX_HOURS * 3600:
                raise TimeoutError("超过最大运行时长")
            
            # 读当前播放进度
            current = self._get_current_time(tab)
            duration = self._get_duration(tab)
            
            if duration <= 0:
                stall_count += 1
                if stall_count > 10:
                    self.logger.warning("视频卡死，跳过")
                    return False
                time.sleep(10)
                continue
            
            progress = current / duration * 100
            self.logger.info(f"⏳ {course.name}: {progress:.1f}%")
            
            # 检测弹窗
            AntiDetect.handle_dialogs(tab)
            
            # 检测是否卡住
            if abs(progress - last_progress) < 0.5:
                stall_count += 1
            else:
                stall_count = 0
            last_progress = progress
            
            if stall_count > 30:  # 5分钟没动
                self.logger.warning("播放卡住，尝试重新播放")
                self._play_video(tab, video_info)
                stall_count = 0
            
            # 完成
            if progress >= 95:
                self.logger.info(f"✅ {course.name}: 播放完成")
                # 等待服务器同步
                time.sleep(30)
                return True
            
            time.sleep(Config.PROGRESS_POLL_SEC)
    
    def _detect_video(self, tab):
        """检测视频（支持跨域iframe）"""
        js = """
        (function() {
            // 1. 主页面video
            var v = document.querySelector('video');
            if(v && v.duration > 0) return {type:'main', duration:v.duration};
            
            // 2. iframe 内video
            var frames = document.querySelectorAll('iframe');
            for(var f of frames) {
                try {
                    var fv = f.contentDocument?.querySelector('video');
                    if(fv && fv.duration > 0) return {type:'iframe', duration:fv.duration};
                } catch(e) {}
            }
            return null;
        })();
        """
        return self.brain.execute_js(tab, js)
    
    def _play_video(self, tab, info):
        """播放视频"""
        js = """
        (function() {
            var v = document.querySelector('video');
            if(!v) {
                var f = document.querySelector('iframe');
                if(f) try { v = f.contentDocument.querySelector('video'); } catch(e) {}
            }
            if(v) {
                v.muted = true;
                v.play();
            }
        })();
        """
        self.brain.execute_js(tab, js)
```

## 5️⃣ anti_detect.py — 反检测层

```python
class AntiDetect:
    """反检测措施"""
    
    @staticmethod
    def inject(tab):
        """注入反检测JS（在导航前执行）"""
        tab.run_js("""
        Object.defineProperty(navigator, 'webdriver', {get:()=>undefined});
        Object.defineProperty(navigator, 'plugins', {get:()=>[1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get:()=>['zh-CN','zh','en']});
        """)
    
    @staticmethod
    def handle_dialogs(tab) -> bool:
        """扫描并关闭所有弹窗"""
        return tab.run_js("""
        var closed = false;
        var keywords = ['继续','确定','确认','已完成','下一节','知道了','好的'];
        var btns = document.querySelectorAll('button,.el-button,.layui-layer-btn a');
        for(var b of btns) {
            var t = b.textContent.trim();
            for(var k of keywords){
                if(t.includes(k)){ b.click(); closed = true; break; }
            }
            if(closed) break;
        }
        return closed;
        """)
    
    @staticmethod
    def prevent_mouse_leave(tab):
        """防止鼠标离开时视频暂停"""
        tab.run_js("""
        document.addEventListener('mouseleave', function(e) { e.stopPropagation(); }, true);
        var v = document.querySelector('video');
        if(v) {
            v.removeEventListener('pause', null);
            v.addEventListener('pause', function(e) { 
                if(this.currentTime < this.duration - 1) this.play(); 
            });
        }
        """)
    
    @staticmethod
    def random_delay():
        """随机延迟，模拟人类操作间隔"""
        time.sleep(random.uniform(*Config.HUMAN_DELAY))
```

## 6️⃣ progress.py — 进度管理层

```python
class ProgressManager:
    """课程进度持久化管理"""
    
    def __init__(self):
        self.db_path = "data/progress.json"
        self._data = self._load()
    
    def _load(self) -> dict:
        path = Path(self.db_path)
        if path.exists():
            return json.loads(path.read_text())
        return {"courses": {}, "history": []}
    
    def save(self, course_id: str, progress: float, status: str = "进行中"):
        self._data["courses"][course_id] = {
            "progress": progress,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        self._flush()
    
    def get_remaining(self) -> list:
        """获取未完成的课程"""
        return [c for c in self._data["courses"].values() 
                if c["progress"] < 100 and c["status"] != "跳过"]
    
    def log_history(self, action: str, detail: str):
        self._data["history"].append({
            "time": datetime.now().isoformat(),
            "action": action,
            "detail": detail
        })
        self._flush()
    
    def _flush(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.db_path).write_text(json.dumps(self._data, ensure_ascii=False, indent=2))
```

## 7️⃣ reporter.py — 报告层

```python
class Reporter:
    """多通道报告"""
    
    def __init__(self):
        self.logger = logging.getLogger("reporter")
    
    def progress(self, tab, done: int, total: int, current: str = ""):
        """进度报告"""
        pct = done / total * 100 if total > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        msg = f"📊 进度: [{bar}] {done}/{total} ({pct:.0f}%) {current}"
        self.logger.info(msg)
    
    def summary(self, report: dict):
        """完成总结"""
        self.logger.info(f"""
        ╔════════════════════════╗
        ║   刷课完成报告         ║
        ╠════════════════════════╣
        ║ 总课程: {report.get('total',0):3d}               ║
        ║ 已完成: {report.get('completed',0):3d}               ║
        ║ 成功率: {report.get('success_rate',0):.0f}%%              ║
        ║ 用时:   {report.get('duration',''):10s}    ║
        ╚════════════════════════╝
        """)
    
    def feishu(self, msg: str):
        """飞书卡片推送"""
        if not Config.FEISHU_WEBHOOK:
            return
        import requests
        requests.post(Config.FEISHU_WEBHOOK, json={"msg_type": "text", 
                     "content": {"text": msg}}, timeout=5)
```

## 8️⃣ quiz.py — 答题模块

```python
class QuizSolver:
    """自动答题 — 识别题目 → 搜索答案 → 填入"""
    
    def __init__(self, brain: BrowserBrain):
        self.brain = brain
    
    def solve(self, tab) -> bool:
        """检测并回答当前页面的测验题"""
        if not self._has_quiz(tab):
            return False
        
        questions = self._extract_questions(tab)
        for q in questions:
            # 1. 本地题库查找
            answer = self._lookup_local(q['text'])
            
            # 2. DeepSeek 推断
            if not answer:
                answer = self._ask_deepseek(f"题目: {q['text']}\n选项: {q['options']}\n请给出正确答案")
            
            # 3. 填入答案
            self._fill_answer(tab, q, answer)
        
        # 提交
        if Config.QUIZ_ENABLED:
            self.brain.click(tab, "button[type='submit']")
        
        # 随机错题（防检测）
        if random.random() > Config.QUIZ_CORRECT_RATE:
            self._intentional_wrong(tab)
        
        return True
```

## 9️⃣ scheduler.py — 调度引擎

```python
class Scheduler:
    """三步模式调度器"""
    
    def __init__(self):
        self.brain = BrowserBrain()
        self.progress = ProgressManager()
        self.reporter = Reporter()
    
    def step_mode(self):
        """步进模式 — 用户说一步做一步"""
        while True:
            cmd = input("下一步? (login/scan/play/quiz/quit): ")
            if cmd == 'login':     self._step_login()
            elif cmd == 'scan':    self._step_scan()
            elif cmd == 'play':    self._step_play()
            elif cmd == 'quit':    break
    
    def auto_mode(self):
        """全自动模式 — 一条龙"""
        self._step_login()
        courses = self._step_scan()
        for course in courses:
            self._step_play(course)
            self.reporter.progress(...)
        self.reporter.summary(...)
    
    def cron_mode(self, schedule_expr: str):
        """定时模式 — 后台定时运行"""
        import croniter
        # 用 Hermes cronjob 管理
```

## 🔟 persistence.py — 持久化层

```python
class SessionManager:
    """登录会话管理 — 免重复登录"""
    
    def __init__(self):
        self.cookie_dir = Path("data/cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, domain: str, tab):
        """保存登录态"""
        cookies = tab.run_js("return document.cookie")
        (self.cookie_dir / f"{domain}.txt").write_text(cookies)
    
    def restore(self, domain: str, tab) -> bool:
        """恢复登录态"""
        path = self.cookie_dir / f"{domain}.txt"
        if not path.exists():
            return False
        cookies = path.read_text()
        tab.run_js(f"document.cookie='{cookies}'")
        return True
```

## 1️⃣1️⃣ plugin.py — 站点插件体系

```python
class SitePlugin(ABC):
    """站点插件 — 每个平台一个"""
    
    name: str
    domains: list[str]
    
    # 已知选择器（加速用，不强制）
    login_selectors: dict = {}
    course_selectors: dict = {}
    video_selectors: dict = {}
    
    # 可选覆盖的方法
    def detect_login(self, brain) -> bool: ...
    def get_courses(self, brain) -> list[Course]: ...
    def detect_video(self, brain) -> dict: ...

class PluginRegistry:
    """插件注册中心"""
    _plugins = {}
    
    @classmethod
    def register(cls, plugin):
        for domain in plugin.domains:
            cls._plugins[domain] = plugin
    
    @classmethod
    def get(cls, domain: str) -> SitePlugin | None:
        for d, p in cls._plugins.items():
            if d in domain:
                return p
        return None
    
    @classmethod
    def detect(cls, brain, tab) -> SitePlugin:
        """自动检测当前页面属于哪个站点"""
        url = brain.read_url(tab)
        for domain, plugin in cls._plugins.items():
            if domain in url:
                return plugin
        return None

# ── 内置插件 ──
class ChinahrtPlugin(SitePlugin):
    name = "chinahrt"
    domains = ["gp.chinahrt.com"]
    login_selectors = {
        'username': 'input[type="text"]',
        'password': 'input[type="password"]',
        'captcha': 'input[name="captcha"]',
        'submit': 'button[type="submit"]',
    }

class HuayiPlugin(SitePlugin):
    name = "huayiwang"
    domains = ["huayiwang.com"]
    login_selectors = {}  # 待补充
```

---

## 完整目录结构

```
auto-study/
│
├── core/
│   ├── __init__.py
│   ├── config.py          # S1 配置管理
│   ├── logger.py           # S2 日志系统
│   ├── exceptions.py       # S3 异常+重试
│   ├── brain.py            # 1. 基础能力层
│   ├── login.py            # 2. 万能登录层
│   ├── scanner.py          # 3. 课程识别层
│   ├── player.py           # 4. 视频播放层
│   ├── anti_detect.py      # 5. 反检测层
│   ├── progress.py         # 6. 进度管理层
│   ├── reporter.py         # 7. 报告层
│   ├── quiz.py             # 8. 答题模块
│   ├── scheduler.py        # 9. 调度引擎
│   ├── persistence.py      # 10. 持久化层
│   └── plugin.py           # 11. 站点插件体系
│
├── plugins/
│   ├── __init__.py
│   ├── chinahrt.py         # 宁夏继续教育
│   ├── huayiwang.py        # 华医网
│   └── template.py         # 插件模板
│
├── data/                   # 运行时数据
│   ├── progress.json       # 进度
│   ├── cookies/            # 登录会话
│   └── quiz_cache.db       # 题库缓存
│
├── logs/                   # 日志输出
│   └── run.log
│
├── scripts/                # 辅助脚本
│   └── install_deps.sh
│
├── launcher.py             # CLI入口
├── requirements.txt        # DrissionPage, ddddocr, httpx, ...
└── README.md
```

## vs 旧架构（v4）的变化

| 变化 | 说明 |
|------|------|
| + config.py | 统一配置管理，不散落在各个模块 |
| + logger.py | 统一日志，控制台+文件双重输出 |
| + exceptions.py | 异常分类 + 自动重试装饰器 |
| brain.py 完善 | 新增 `analyze_screenshot` + `execute_js`，去掉直接调 API |
| login.py 完善 | 双路径：已知选择器直接填 / 未知站点 AI 分析 |
| player.py 完善 | 新增卡死检测、超时控制、自动重试 |
| anti_detect.py 完善 | 新增防鼠标离开暂停 |
| quiz.py 完善 | 新增本地题库查找、随机错题 |
| scheduler.py 完善 | 三步模式详细化 |
| persistence.py 完善 | Cookie 持久化 |
| plugin.py 完善 | 插件注册中心 + 自动检测 |

## 工作流（以 chinahrt 为例）

```
用户: "帮我刷宁夏继续教育，账号xxx，密码yyy"

launcher.py
  ├─ config.load()               → 加载账号配置
  ├─ logger.setup()              → 开启日志
  ├─ brain = BrowserBrain()      → 连接 Edge:9223
  ├─ login.login("chinahrt", ...) → 自动登录
  │   ├─ brain.navigate(login_url)
  │   ├─ brain.analyze_screenshot() → 截图分析
  │   ├─ input_text(username/password)
  │   ├─ _handle_captcha()       → ddddocr 识别验证码
  │   └─ verify login success
  ├─ scanner.scan(tab1)          → 列出未完成课程
  │   ├─ brain.read_text()
  │   ├─ brain.analyze_screenshot()
  │   └─ DeepSeek 解析课程列表
  ├─ for course in courses:
  │   ├─ player.play(tab3, course) → 播视频
  │   │   ├─ detect_video (iframe)
  │   │   ├─ inject anti-detect
  │   │   ├─ play muted
  │   │   ├─ monitor progress
  │   │   └─ handle dialogs
  │   ├─ quiz.solve(tab2)        → 自动答题（如果有）
  │   └─ progress.save(course.id, 100%)
  ├─ reporter.summary()          → 输出总结
  │   ├─ 总课程/已完成/成功率/用时
  │   └─ feishu webhook（可选）
  └─ persistence.save_cookies()  → 保存登录态
```
