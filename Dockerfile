FROM python:3.10

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app

ENV MONGO_URI ""

EXPOSE 8000
CMD ["hypercorn", "app.py", "--bind", "0.0.0.0"]