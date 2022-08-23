FROM silkeh/clang:14

WORKDIR /workspace

RUN echo "#include <iostream>\n\nint main() {\n\tstd::cout << \"Hello World\" << std::endl;\n}" > main.cpp \
    && apt-get update -y --fix-missing \
    && apt-get -y install -f gdb \
    && apt-get -y install -f gdbserver \
    && apt-get -y install -f net-tools 

CMD /bin/bash
