# 第一阶段：构建环境（使用 Node.js 镜像）
FROM node:18-alpine AS builder

WORKDIR /app

# 1. 先拷贝依赖描述文件
COPY package*.json ./

# 2. 安装项目依赖
RUN npm install

# 3. 拷贝前端所有源码
COPY . .

# 4. 执行打包命令（生成 dist 文件夹）
# 注意：Vite 会根据 .env.production 里的配置把 API 地址写进代码
RUN npm run build

# 第二阶段：运行环境（使用 Nginx 镜像）
FROM nginx:alpine

# 5. 从第一阶段生成的 builder 中，把打包好的 dist 目录拷贝到 Nginx 的网页目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 6. 拷贝我们自定义的 Nginx 配置文件，覆盖默认配置
# 这一步非常重要，它决定了请求怎么转发到后端
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 7. 暴露 80 端口
EXPOSE 80

# 8. 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]