FROM ubuntu:latest
LABEL authors="Tobias Obwexer"
# Use the official Python image
FROM python:3.12

# Set the working directory
WORKDIR /

# Copy the project files into the container
COPY . /

# Install dependencies
RUN pip install -r requirements.txt

# Expose the Streamlit default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501"]