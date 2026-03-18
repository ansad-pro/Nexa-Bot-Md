FROM node:20-bullseye

WORKDIR /usr/src/app

# Copy only package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Default command
CMD ["node", "main.js"]
