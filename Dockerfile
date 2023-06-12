# Python 3.11
FROM python:3.11-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY .. /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 8000

# Run main.py when the container launches
#CMD ["python", "main.py"]

# Run uvicorn when the container launches
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]


