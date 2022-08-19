FROM python:3.9

WORKDIR /workspace

RUN echo "print(\"hello world\")" > /workspace/main.py \
    && apt-get -y update \
    && apt-get -y install telnet \
    && pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install remote_pdb 

CMD /bin/bash
