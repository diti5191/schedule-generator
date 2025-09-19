FROM node:20-alpine

WORKDIR /app
COPY package.json ./
COPY server.mjs ./
COPY src ./src
COPY public ./public
COPY tests ./tests

EXPOSE 4173
CMD ["npm", "start"]