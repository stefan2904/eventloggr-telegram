FROM python:3.4

WORKDIR /usr/src/app
COPY ./src/requirements.txt ./

RUN pip install -r requirements.txt
COPY ./src/ ./

EXPOSE 5000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]
CMD ["sh", "startapp.sh"]
