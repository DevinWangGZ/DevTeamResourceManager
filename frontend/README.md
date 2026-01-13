# DevTeam Manager Frontend

前端应用，基于Vue 3 + TypeScript + Vite开发。

## 技术栈

- Vue 3.4+
- TypeScript 5.3+
- Vite 5.0+
- Element Plus 2.4+
- Pinia 2.1+
- Vue Router 4.2+
- Axios 1.6+
- ECharts 5.4+

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env.development

# 编辑.env.development文件，配置API地址
```

### 3. 运行开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 4. 构建生产版本

```bash
npm run build
```

## 开发命令

```bash
# 开发服务器
npm run dev

# 构建
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint

# 代码格式化
npm run format

# 单元测试
npm run test:unit
```

## 项目结构

```
frontend/
├── src/
│   ├── modules/      # 业务模块
│   ├── components/   # 公共组件
│   ├── stores/       # Pinia store
│   ├── router/       # 路由配置
│   ├── api/          # API接口层
│   └── ...
└── ...
```
