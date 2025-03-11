# Use official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8001

# Run the FastAPI app
CMD ["uvicorn", "test_service:app", "--host", "0.0.0.0", "--port", "8001"]
