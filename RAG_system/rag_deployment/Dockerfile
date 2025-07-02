FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# 安裝 serve 來運行靜態文件
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"] 