FROM gradle:8.10.2-jdk21-alpine AS build

COPY --chown=gradle:gradle . /home/gradle/src
WORKDIR /home/gradle/src

RUN gradle clean build --no-daemon

FROM openjdk:24-jdk-slim

WORKDIR /app
COPY --from=build /home/gradle/src/build/libs/default-0.1-all.jar .

ENTRYPOINT ["java", "-jar", "default-0.1-all.jar"]
