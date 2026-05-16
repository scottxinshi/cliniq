# ClinIQ — Streamlit frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (Docker caches this layer if unchanged)
COPY requirements.txt .

# Install all packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Generate OMOP database
RUN mkdir -p data && python scripts/generate_omop_data.py

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
