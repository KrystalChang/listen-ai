FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 8000

ENV GATEWAY_PORT=8000
ENV STAT_URL=http://stat:8002
ENV NLP_URL=http://nlp:8001
ENV JWT_SECRET=supersecret
ENV DEMO_USER=admin
ENV DEMO_PASS=admin123

CMD ["npm", "run", "dev"]