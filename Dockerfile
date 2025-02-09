# syntax=docker/dockerfile:1

# Use a slim Python image with the specified version.
ARG PYTHON_VERSION=3.13.2
FROM python:${PYTHON_VERSION}-slim AS base

# Prevent Python from writing pyc files and disable output buffering.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /app

# Create a non-privileged user to run the application.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy the dependency file and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Switch to the non-privileged user.
USER appuser

# Expose the port your Flask app listens on.
EXPOSE 5000

# Start the application with Gunicorn.
# Ensure that your main Flask file is named "app.py" and it defines a variable "app".
CMD ["gunicorn", "-w", "1", "app:app", "--bind", "0.0.0.0:5000"]
