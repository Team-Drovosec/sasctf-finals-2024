FROM openjdk:21

COPY . /server
WORKDIR /server

ENTRYPOINT ["java", "-Xms6000M", "-Xmx6000M", "-XX:+AlwaysPreTouch", "-XX:+DisableExplicitGC", "-XX:+ParallelRefProcEnabled", "-XX:+PerfDisableSharedMem", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC", "-XX:G1HeapRegionSize=8M", "-XX:G1HeapWastePercent=5", "-XX:G1MaxNewSizePercent=40", "-XX:G1MixedGCCountTarget=4", "-XX:G1MixedGCLiveThresholdPercent=90", "-XX:G1NewSizePercent=30", "-XX:G1RSetUpdatingPauseTimePercent=5", "-XX:G1ReservePercent=20", "-XX:InitiatingHeapOccupancyPercent=15", "-XX:MaxGCPauseMillis=200", "-XX:MaxTenuringThreshold=1", "-XX:SurvivorRatio=32", "-Dminecraft.api.env=custom", "-Dminecraft.api.auth.host=http://axel-auth:25566/auth", "-Dminecraft.api.account.host=http://axel-auth:25566/account", "-Dminecraft.api.session.host=http://axel-auth:25566/session", "-Dminecraft.api.services.host=http://axel-auth:25566/services", "-jar", "paper.jar", "nogui"]