
FROM ubuntu:18.04

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y python3
RUN apt-get install -y python3-pip
#Install git
RUN apt-get install git -y
RUN git clone -b v0.18.0 https://Xing-Huang:13583744689edc@github.com/palliums-developers/libra-client.git
RUN cp ./libra-client/violas_client /usr/local/lib/python3.6/dist-packages/ -rf

WORKDIR .
RUN mkdir app
COPY . /app/
RUN pip3 install -r /app/requirements.txt

CMD ["python3", "/app/app.py"]



