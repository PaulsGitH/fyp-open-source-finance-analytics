FROM python:3.13.7-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir streamlit pandas numpy requests python-dotenv
COPY app ./app
COPY data ./data
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
