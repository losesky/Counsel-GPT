
## Counsel-GPT - 基于本地知识库的 langchain + ChatGLM2-6B-int4 的大语言模型在法律方面的应用实现

## 基本介绍

利用 [langchain](https://github.com/hwchase17/langchain) 思想实现的基于本地知识库的法律知识问答应用。目标期望建立一套能离线运行，基于开源模型，中文支持友好的专业法律知识问答解决方案。

本项目中 Embedding 默认选用的是 [GanymedeNil/text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese/tree/main)，LLM 默认选用的是 [ChatGLM2-6B-int4](https://github.com/THUDM/ChatGLM2-6B)。依托上述模型，本项目可实现全部使用**开源**模型**离线私有部署**。

## 硬件需求

- ChatGLM2-6B-int4 模型硬件需求
  
    | **量化等级**   | **最低 GPU 显存**（推理） | **最低 GPU 显存**（高效参数微调） |
    | -------------- | ------------------------- | --------------------------------- |
    | INT4           | 6 GB                      | 7 GB                              |

- Embedding 模型硬件需求

    本项目中默认选用的 Embedding 模型 [GanymedeNil/text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese/tree/main) 约占用显存 3GB，也可修改为在 CPU 中运行。

## Docker 部署

为了能让容器使用主机GPU资源，需要在主机上安装 [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)。具体安装步骤如下：
```shell
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit-base
sudo systemctl daemon-reload 
sudo systemctl restart docker
```
安装完成后，可以使用以下命令编译镜像和启动容器：
```
docker build -f Dockerfile -t counsel-gpt:latest .
docker run --gpus all -d --name counsel-gpt -p 8080:8080  counsel-gpt:latest

```

## 软件需求

本项目已在 Python 3.8.1 - 3.10，CUDA 11.7 环境下完成测试。已在 Windows、ARM 架构的 macOS、Linux 系统中完成测试。

Web UI 可以实现如下功能：

1. 运行前自动读取`configs/model_config.py`中`LLM`及`Embedding`模型枚举及默认模型设置运行模型，如需重新加载模型，可在 `模型配置` Tab 重新选择后点击 `重新加载模型` 进行模型加载；
2. 可手动调节保留对话历史长度、匹配知识库文段数量，可根据显存大小自行调节；
3. `对话` Tab 具备模式选择功能，可选择 `通用对话` 与 `专业问答` 模式进行对话，支持流式对话；
4. 添加 `配置知识库` 功能，支持选择已有知识库或新建知识库，并可向知识库中**新增**上传文件/文件夹，使用文件上传组件选择好文件后点击 `上传文件并加载知识库`，会将所选上传文档数据加载至知识库中，并基于更新后知识库进行问答；
5. 新增 `知识库检索` Tab，可用于测试不同文本切分方法与检索相关度阈值设置。

## 如何制作docker镜像

1. 构造镜像

docker build -f Dockerfile -t counsel-gpt:latest .

2. 登陆阿里云镜像管理器

docker login --username=losesky77 registry.cn-shenzhen.aliyuncs.com

3. 将刚才构建的镜像标记版本

docker tag counsel-gpt:latest registry.cn-shenzhen.aliyuncs.com/losesky/counsel_gpt:1.0.0

4. 将标记版本的镜像上传阿里云镜像管理器
   
docker push registry.cn-shenzhen.aliyuncs.com/losesky/counsel_gpt:1.0.0

## 清理系统相关命令

sudo docker system prune

sudo docker container ls -a

sudo docker image ls -a

sudo docker container rm <container_id>

sudo docker image rm <image_id>

sudo apt-get clean

sudo apt-get autoclean

sudo apt-get autoremove

## 最简单方式

./clear_docker.sh





