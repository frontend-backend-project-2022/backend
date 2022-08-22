FROM gcc:8.3

WORKDIR /workspace

RUN echo "#include <iostream>\n\nint main() {\n\tstd::cout << \"Hello World\";\n}" > main.cpp \
    && apt-get update -y\
    && apt-get -y install gdb \
    && apt-get -y install gdbserver \
    && apt-get -y install -f net-tools
CMD /bin/bash
