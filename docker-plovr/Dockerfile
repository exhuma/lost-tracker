FROM anapsix/alpine-java:7_jdk
RUN apk update
RUN apk add wget
ADD md5sums.txt /tmp
RUN wget -O /tmp/apache-ant-1.9.9-src.tar.gz \
    http://apache.javapipe.com//ant/source/apache-ant-1.9.9-src.tar.gz
RUN cd /tmp && md5sum -c md5sums.txt
RUN cd /opt && \
    tar xzf /tmp/apache-ant-1.9.9-src.tar.gz && \
    rm /tmp/apache-ant-1.9.9-src.tar.gz
RUN cd /opt/apache-ant-1.9.9 && ./build.sh

ENV JAVA_HOME /opt/jdk
ENV ANT_HOME /opt/apache-ant-1.9.9/dist

RUN apk add git
RUN mkdir /libs
RUN cd /libs && git clone https://github.com/bolinfest/plovr.git
RUN cd /libs && git clone -v https://github.com/google/closure-library.git
RUN cd /libs/plovr && git checkout -q 9f12b6c
RUN cd /libs/closure-library && git checkout -q 57bdfe0093c
RUN cd /opt/apache-ant-1.9.9 && ./dist/bin/ant -f fetch.xml -Ddest=system
RUN cd /libs/plovr && ANT_OPTS=-Dfile.encoding=UTF8 /opt/apache-ant-1.9.9/dist/bin/ant build
ENTRYPOINT ["/opt/jdk/bin/java", "-jar", "/libs/plovr/build/plovr.jar"]
