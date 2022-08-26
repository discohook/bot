FROM node:16

RUN apt update && apt -y install git python3 build-essential

ENV NODE_ENV production

WORKDIR /usr/src/app

COPY .yarnrc.yml package.json yarn.lock ./
COPY .yarn ./.yarn
RUN yarn install --immutable

COPY . .
RUN yarn run build

CMD [ "node", "dist/index.js" ]
