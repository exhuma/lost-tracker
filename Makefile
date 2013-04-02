PLOVR=/home/exhuma/work/__libs__/plovr.jar

all:
	java -jar ${PLOVR} build plovr-config.js

run:
	java -jar ${PLOVR} serve plovr-config.js

