FROM openjdk:21

COPY . /proxy
WORKDIR /proxy

ENTRYPOINT ["java", "-XX:+UseG1GC", "-XX:G1HeapRegionSize=4M", "-XX:+UnlockExperimentalVMOptions", "-XX:+ParallelRefProcEnabled", "-XX:+AlwaysPreTouch", "-XX:MaxInlineLevel=15", "-Dmojang.sessionserver=http://axel-auth:25566/session/session/minecraft/hasJoined", "-jar", "velocity.jar"]