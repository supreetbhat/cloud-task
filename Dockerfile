# 1. Get a lightweight Linux machine with Python pre-installed
FROM python:3.12-slim

# 2. Create a folder named /app inside the container and move into it
WORKDIR /app

# 3. Copy our requirements list from your Mac into the container
COPY requirements.txt .

# 4. Install the Python packages inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of our code (main.py, etc.) into the container
COPY . .

# 6. Tell the container what command to run when it wakes up
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]