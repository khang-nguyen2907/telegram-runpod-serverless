FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Python dependencies
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt install --yes --no-install-recommends\
    wget\
    bash\
    openssh-server \
    software-properties-common &&\
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install python3.10 python3-pip -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
    
RUN pip install --upgrade pip && \
    pip install safetensors==0.3.1 sentencepiece huggingface_hub \
        git+https://github.com/winglian/runpod-python.git@fix-generator-check ninja==1.11.1

RUN mkdir data 
WORKDIR /data

COPY requirements.txt /data/requirements.txt
RUN pip install -r /data/requirements.txt
RUN pip install -U git+https://github.com/huggingface/transformers.git

COPY handler.py /data/handler.py
COPY __init__.py /data/__init__.py

ENV MODEL_NAME="TheBloke/dolphin-2.5-mixtral-8x7b-GPTQ"
ENV MODEL_REPO="/data/model"
ENV HUGGING_FACE_HUB_TOKEN="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"
ENV HUGGINGFACE_HUB_CACHE="/runpod-volume/huggingface-cache/hub"
ENV TRANSFORMERS_CACHE="/runpod-volume/huggingface-cache/hub"

RUN mkdir $MODEL_REPO
RUN huggingface-cli download $MODEL_NAME --token $HUGGING_FACE_HUB_TOKEN --local-dir=$MODEL_REPO --local-dir-use-symlinks False

CMD ["python", "-m", "handler"]