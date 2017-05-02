FROM isuper/java-oracle:jdk_7
RUN apt-get update && apt-get install -y git ant
RUN mkdir /libs
RUN cd /libs && git clone https://github.com/bolinfest/plovr.git
RUN cd /libs && git clone https://github.com/google/closure-library.git
RUN cd /libs/plovr && git checkout -q 9f12b6c
RUN cd /libs/closure-library && git checkout -q 57bdfe0093c
RUN cd /libs/plovr && ANT_OPTS=-Dfile.encoding=UTF8 ant build
ENTRYPOINT ["/usr/bin/java", "-jar", "/libs/plovr/build/plovr.jar"]
