FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/transactions
RUN npm run build
EXPOSE 3000
CMD ["sh", "-c", "npm start -- -p ${PORT:-3000}"]
