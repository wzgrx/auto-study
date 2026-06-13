# 代码审查结果 — 逐行对比分析

对比源：旧 chinahrt 项目 cdp_connection.py | PyDoll connection_handler.py | BrowserStack docs

## tab_manager.py（6个问题）

| 行 | 问题 | 严重 | 修复方案 |
|----|------|:----:|---------|
| 100 | `navigate()` 无超时 | ⚠️ | 旧项目有 `timeout` 参数，DrissionPage tab.get 可能卡死 |
| 107 | `navigate_hash()` 用 f-string 拼 hash | ✅ 低风险 | hash_str 来自配置，无用户输入 |
| 114-130 | `_refresh_cache()` 吞所有异常 | ⚠️ | 至少应 `log.warning` |
| 77-79 | 策略4空白页匹配只查固定列表 | ⚠️ | 应加 `or not t.url.strip()` |
| 81-83 | 策略5返回第一个标签页可能在无关页 | ⚠️ | 应先查有空白页的，最后才用第一个 |
| 136-144 | `close_all()` pass 不报错 | ℹ️ | 可用 |

## brain.py（3个问题）

| 行 | 问题 | 严重 | 修复方案 |
|----|------|:----:|---------|
| 25-26 | `read_text()` 无异常处理 | ❌ | 如果 body 为空会 AttributeError |
| 39-58 | `analyze_screenshot()` 无重试 | ⚠️ | Gemma 可能超时，应重试1次 |
| 62-72 | `js_call()` 写好了但无人调用 | ℹ️ | 留用，以后 input_text/click 可改用 |

## login.py（2个问题）

| 行 | 问题 | 严重 | 修复方案 |
|----|------|:----:|---------|
| 67-69 | `_check_logged_in` 中 `tab.url` 可能 None | ❌ | `(tab.url or "")` |
| 80-84 | `_refresh_captcha` 点击验证码，但 chinahrt 验证码是参数刷新 | ⚠️ | 应刷新 img.src |

## plugin.py（1个问题）

| 行 | 问题 | 严重 | 修复方案 |
|----|------|:----:|---------|
| 52 | `submit: ("button", 1)` 第一个button不一定是登录 | ❌ | 改用文本匹配或其他方式 |
