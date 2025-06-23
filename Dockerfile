# Use a slim Python base image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code and session file
COPY src ./src
COPY anon.session .

# Change ownership of the app directory
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Set the command to run the application
CMD ["python", "-m", "src.main"]