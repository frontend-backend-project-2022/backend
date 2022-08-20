FROM python:3.8

WORKDIR /workspace

RUN echo "print(\"hello world\")" > /workspace/main.py \
    && apt-get update \
    && apt-get -y install -f telnet \
    && pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install remote_pdb

CMD /bin/bash
