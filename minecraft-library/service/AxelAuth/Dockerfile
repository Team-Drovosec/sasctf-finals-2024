FROM openjdk:21

WORKDIR /app
COPY app.jar .

ENTRYPOINT ["java", "-Dmicronaut.server.port=25566", "-jar", "app.jar"]
