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

# 构建 Docker 镜像时，apt-get 源将被修改为指定的镜像源
# RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装Python 3.8.10
# RUN apt-get update && apt-get install -y software-properties-common
# RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.8 python3.8-dev python3-pip nano git

# 设置Python 3.8.10作为默认Python版本
# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# 复制其他文件到镜像中
COPY agent /home/counsel-gpt/agent
COPY assets /home/counsel-gpt/assets
COPY chains /home/counsel-gpt/chains
COPY configs /home/counsel-gpt/configs
COPY loader /home/counsel-gpt/loader
COPY models /home/counsel-gpt/models
COPY module /home/counsel-gpt/module
COPY package /home/counsel-gpt/package
COPY templates /home/counsel-gpt/templates
COPY textsplitter /home/counsel-gpt/textsplitter
COPY utils /home/counsel-gpt/utils
COPY vectorstores /home/counsel-gpt/vectorstores
COPY webui.py /home/counsel-gpt/
COPY requirements.txt /home/counsel-gpt/

WORKDIR /home/counsel-gpt

# RUN python3 -m venv myenv
# RUN /bin/bash -c "source myenv/bin/activate && pip install wheel torch torchvision tensorboard cython -i https://pypi.tuna.tsinghua.edu.cn/simple/"
# RUN /bin/bash -c "source myenv/bin/activate && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/"

# CMD ["/bin/bash", "-c", "source .venv/bin/activate && python3 webui.py --no-remote-model"]


RUN pip install wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# CMD ["python3", "webui.py --no-remote-model"]
# CMD python3 webui.py --no-remote-model
CMD ["python3", "-u", "webui.py"]