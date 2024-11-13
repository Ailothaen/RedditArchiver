FROM python

WORKDIR /app
COPY src .

RUN pip install -r requirements.txt

EXPOSE 80:80
CMD ["gunicorn", "wsgi:app", "-b", "0.0.0.0:80", "-w", "1"]