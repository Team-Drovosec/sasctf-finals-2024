# Use a builder image to build the Go application
FROM golang:alpine AS builder

# Set the working directory to /app
WORKDIR /app

# Copy the Go source code into the container
COPY ./go.mod /app

# Install dependencies
RUN go mod download 

COPY . /app

# Build the Go application
RUN go build -o main ./cmd/main.go

# Create a new image from the builder image
FROM alpine:latest

# Copy the built executable from the builder image
COPY --from=builder /app/main /main

# Expose the port the application will run on
EXPOSE 3134

# Run the command to start the application when the container launches
CMD ["./main"]
