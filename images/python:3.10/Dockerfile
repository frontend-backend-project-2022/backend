FROM python:3.10

WORKDIR /workspace

RUN echo "print(\"hello world\")" > /workspace/main.py \
    && pip install --upgrade pip -i https://tuna.tsinghua.edu.cn/pipy/simple  \
    && pip install remote_pdb

CMD /bin/bash