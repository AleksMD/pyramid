FROM python:3.7
COPY . /app
WORKDIR app/
RUN python setup.py install
EXPOSE 6543
