FROM ubuntu:20.04

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

# FROM ubuntu:20.04
MAINTAINER "Counsel-GPT"

# 构建 Docker 镜像时，apt-get 源将被修改为指定的镜像源
# RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装Python 3.8.10
# RUN apt-get update && apt-get install -y software-properties-common
# RUN add-apt-repository ppa:deadsnakes/ppa
# RUN apt-get update && apt-get install -y python3.8 python3.8-dev python3-pip python3-venv

# 设置Python 3.8.10作为默认Python版本
# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# 复制其他文件到镜像中
# COPY agent /Counsel-GPT/agent
# COPY assets /Counsel-GPT/assets
# COPY chains /Counsel-GPT/chains
# COPY configs /Counsel-GPT/configs
# COPY loader /Counsel-GPT/loader
# COPY models /Counsel-GPT/models
# COPY module /Counsel-GPT/module
# COPY nltk_data /Counsel-GPT/nltk_data
# COPY templates /Counsel-GPT/templates
# COPY textsplitter /Counsel-GPT/textsplitter
# COPY utils /Counsel-GPT/utils
# COPY vectorstores /Counsel-GPT/vectorstores
# COPY webui.py /Counsel-GPT/
# COPY requirements.txt /Counsel-GPT/
# 加载模型
# COPY LLMs /Counsel-GPT/LLMs
# COPY embeddings /Counsel-GPT/embeddings

COPY . /Counsel-GPT/

WORKDIR /Counsel-GPT

# RUN python3 -m venv myenv
# RUN /bin/bash -c "source myenv/bin/activate && pip install wheel torch torchvision tensorboard cython -i https://pypi.tuna.tsinghua.edu.cn/simple/"
# RUN /bin/bash -c "source myenv/bin/activate && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/"

CMD ["/bin/bash", "-c", "source myenv/bin/activate && ls && python3 webui.py --no-remote-model"]


# RUN pip install wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/
# RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# CMD ["python3", "webui.py --no-remote-model"]
# CMD python3 webui.py --no-remote-model
# CMD ["python3", "-u", "webui.py --no-remote-model"]
# CMD ll