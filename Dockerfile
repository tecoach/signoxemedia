FROM python:3.6
ENV PYTHONUNBUFFERED 1
ENV DEBUG True
EXPOSE 4000
RUN mkdir /app
WORKDIR /app
ADD requirements.pip /app/
RUN pip install -r requirements.pip
ADD . /app/
RUN python manage.py migrate
ENTRYPOINT ["python", "manage.py", "runserver", "0:4000"]
