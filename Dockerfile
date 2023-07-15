FROM  nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Disable prompt of apt
ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN mv /etc/apt/sources.list /etc/apt/sources_backup.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal universe " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates universe " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal multiverse " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates multiverse " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security universe " >> /etc/apt/sources.list && \
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security multiverse " >> /etc/apt/sources.list && \
echo "deb http://archive.canonical.com/ubuntu focal partner " >> /etc/apt/sources.list

MAINTAINER "Counsel-GPT"

# install Python 3.8.10
RUN apt-get update && apt-get install -y python3.8 python3.8-dev python3-pip nano git

# copy to docker image
COPY agent /home/counsel-gpt/agent
COPY assets /home/counsel-gpt/assets
COPY chains /home/counsel-gpt/chains
COPY configs /home/counsel-gpt/configs
COPY loader /home/counsel-gpt/loader
COPY models /home/counsel-gpt/models
COPY module /home/counsel-gpt/module
COPY nltk_data /home/counsel-gpt/nltk_data
COPY package /home/counsel-gpt/package
COPY templates /home/counsel-gpt/templates
COPY textsplitter /home/counsel-gpt/textsplitter
COPY utils /home/counsel-gpt/utils
COPY vectorstores /home/counsel-gpt/vectorstores
COPY webui.py /home/counsel-gpt/
COPY requirements.txt /home/counsel-gpt/
COPY utils/chromedriver /usr/bin/chromedriver

WORKDIR /home/counsel-gpt

# install driver
RUN chmod +x /usr/bin/chromedriver
RUN apt-get install /home/counsel-gpt/utils/google-chrome-stable_current_amd64.deb -y

# install requirements
RUN pip install wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# docker first cmd
CMD ["python3", "-u", "webui.py"]