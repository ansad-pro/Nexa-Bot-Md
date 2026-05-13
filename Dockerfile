FROM node:20-bullseye-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY package*.json ./

RUN npm install --production

COPY . .

CMD ["node", "nexa.js"]
