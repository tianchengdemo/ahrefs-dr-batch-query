# Changelog

## v2.3.0

- API 增加 Cookie 内存缓存，默认复用 30 分钟
- API 增加 SQLite 结果缓存，默认保留 30 天
- 批量查询只实时请求未命中的域名
- 修正文档中的 Bot 启动方式为 `python -m bot.main`
- 新增 `result_cache.py`
- 删除无用调试脚本和一次性测试脚本
