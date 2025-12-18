
# Use Python 3.9
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install dependencies
# Install build-essential for some python packages if needed
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 7860 (Hugging Face default) or 8000
EXPOSE 7860

# Command to run the application
# Note: We use the port environment variable or default to 7860
CMD ["uvicorn", "shl_recommender.src.app:app", "--host", "0.0.0.0", "--port", "7860"]
