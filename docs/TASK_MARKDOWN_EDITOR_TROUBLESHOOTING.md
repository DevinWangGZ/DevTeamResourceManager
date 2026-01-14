# 任务Markdown编辑器问题排查指南

## 问题：图片上传后无法预览，404错误

### 问题描述
上传图片后，返回的URL是 `http://localhost:8000/uploads/images/xxx.png`，但访问时返回404错误。

### 已修复的问题

1. **路径计算不一致**
   - **问题**：`upload.py` 和 `main.py` 使用不同的路径计算方式，导致文件保存位置和静态文件服务目录不一致
   - **修复**：创建统一的路径工具模块 `app/utils/paths.py`，确保所有地方使用相同的路径计算逻辑

2. **静态文件服务挂载顺序**
   - **问题**：静态文件服务在路由注册之后挂载，可能被路由拦截
   - **修复**：将静态文件服务挂载移到路由注册之前

### 验证步骤

1. **检查上传目录是否存在**
   ```bash
   ls -la backend/uploads/images/
   ```

2. **检查文件是否成功保存**
   ```bash
   # 上传一张图片后，检查文件是否存在
   ls -la backend/uploads/images/ | grep ".png"
   ```

3. **检查静态文件服务配置**
   - 查看后端日志，应该看到：`静态文件服务已挂载: /path/to/backend/uploads`
   - 如果看到警告，说明挂载失败

4. **测试静态文件访问**
   ```bash
   # 直接访问图片URL
   curl http://localhost:8000/uploads/images/xxx.png
   ```

### 如果仍然404，检查以下内容

1. **后端服务是否重启**
   - 修改代码后需要重启后端服务
   - 使用 `uvicorn app.main:app --reload` 会自动重启

2. **文件是否真的保存成功**
   - 检查 `backend/uploads/images/` 目录
   - 查看后端日志，确认上传成功

3. **URL路径是否正确**
   - 上传API返回的URL应该是：`/uploads/images/xxx.png`
   - 前端访问时应该是：`http://localhost:8000/uploads/images/xxx.png`

4. **静态文件服务是否正确挂载**
   - 查看后端启动日志
   - 确认没有挂载失败的警告

### 调试方法

1. **添加日志**
   在 `upload.py` 中添加日志：
   ```python
   logger.info(f"文件保存路径: {file_path}")
   logger.info(f"文件URL: {file_url}")
   ```

2. **检查路径**
   在 `main.py` 中添加日志：
   ```python
   logger.info(f"静态文件目录: {uploads_base_dir}")
   logger.info(f"目录是否存在: {uploads_base_dir.exists()}")
   ```

3. **测试文件访问**
   手动创建一个测试文件：
   ```bash
   echo "test" > backend/uploads/images/test.txt
   curl http://localhost:8000/uploads/images/test.txt
   ```

### 常见问题

**Q: 文件上传成功，但访问404？**
A: 检查静态文件服务是否正确挂载，路径是否一致

**Q: 静态文件服务挂载失败？**
A: 检查目录权限，确保有读写权限

**Q: 路径计算错误？**
A: 使用统一的路径工具函数 `app.utils.paths`

### 修复后的代码结构

```
backend/
├── app/
│   ├── utils/
│   │   └── paths.py          # 统一的路径工具（新建）
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── upload.py  # 使用paths工具
│   └── main.py                # 使用paths工具
└── uploads/
    └── images/                # 图片存储目录
```

### 验证修复

修复后，应该能够：
1. ✅ 上传图片成功
2. ✅ 文件保存到正确位置
3. ✅ 通过URL访问图片
4. ✅ 在Markdown编辑器中预览图片

---

**最后更新**：2024-12
