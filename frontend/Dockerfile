#Use official node 20 image as base image
FROM node:20.19.6 as base

#Set the working directory to /app
WORKDIR /app

##Copy the package.json file from current directory into container at /app
COPY package*.json ./

#Install needed packages specified in package.json
# RUN npm ci --legacy-peer-deps
RUN npm install

#Copy all files and directories from host's current directory into /app
COPY . .

#expose port 3000
EXPOSE 3000

#start development server
CMD npm run dev