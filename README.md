### **注意**：请在 linux 环境下运行，`pty, select`模块在 Windows 下不能正常工作

- `flask run`启动应用

- 或是用`python app.py`以调试模式启动应用

- 可以更改`views`下的文件，`views/{module}.py`的 API 将放在`localhost:5000/{module}`前缀下（具体参见`app.py`中的`app.register_blueprint`语句）。

- 例如访问`localhost:5000/docker/`可以看到`docker`模块的 API

- Xterm.js Demo 连接的 Docker Container 根据的是 username 对应的 container.id
  
  - `["docker", "exec", "-it", containerid, "bash"]`(详见 app.py)
  
  - username 目前硬编码为前端\src\views\TerminalView.vue 内的"Dave"。如果该用户名曾经访问过 ternimal，则读取上次的 container；否则创建一个新 container 且 name 设定为 username

- docker 安装详见[菜鸟教程](https://www.runoob.com/docker/ubuntu-docker-install.html)

- database 采用 sqlite3，用户表名称为users，容器表名称为containers(每个容器对应一个项目，一个用户可拥有多个项目)，形式如下:
  
  - ```sqlite
    TABLE users
            (
                id INTEGER AUTO_INCREMENT,
                username TEXT NOT NULL UNIQUE,
                pwhash TEXT NOT NULL,
                PRIMARY KEY(username)
            );
    TABLE containers
            (
                id INTEGER AUTO_INCREMENT,
                containerid TEXT NOT NULL,
                time DATETIME NOT NULL,
                username TEXT,
                FOREIGN KEY(username) REFERENCES users(username),
                PRIMARY KEY(id)
            );
    ```
  
  - 注：pwhash 是 password 经过 sha256 加盐 hash 得到的

如果安装了新的库记得更新`requirements.txt`，有什么进展也可以写在`README`里。

- 08/04；添加了CI，提交时用flake8检查并格式化Python代码，并执行`tests/`文件夹下的测试用例

- 08/09：添加了vscode显示文件测试覆盖率的支持，需要`Coverage Gutters`插件，运行测试后，点击左下角的`Watch`按钮，即可在代码编辑器中查看语句的测试覆盖情况

- 08/16：添加了docker的镜像，最好提前在本地下载gcc:8.3/python:3.8/python3.9/python3.10的镜像

- 08/19：C/C++ 语言服务器
  
  - 安装：`sudo apt-get update && sudo apt-get install clangd`

- 错误信息：
  
  - login：
    - check_logged_in：200 if logged in else 401
    - login：200 if success else 401
    - register（POST）：
      - 用户名已存在：400
      - 注册失败：500
      - 成功：201
    - register（DELETE）：
      - 用户名密码验证失败：401
      - 删除失败：500
      - 成功：200
  - database：
    - db_createProject:
      - 未登录（sessions['username']不存在）：401
      - 项目参数缺失（但可以为空）：400
      - 创建失败：500
      - 成功：201
    - db_getAllProjects：
      - 未登录（sessions['username']不存在）：401
      - 项目参数缺失（但可以为空）：400
      - 创建失败：500
      - 成功：200
    - db_getProject、db_deleteProject、db_updateProject：200 if success else 500
  - dockers：
    - docker_bash、docker_getdir：200 if success else 500
    - docker_upload_file、docker_upload_folder:
      - 没有文件或其他项目参数缺失（但可以为空）：400
      - 失败：500
      - 成功：201
    - docker_upload_content：201 if success else 500
    - docker_download_content：
      - 项目参数缺失（但可以为空）：400
      - 失败：500
      - 成功：200
    - docker_download_file、docker_download_folder：
      - 项目参数缺失（但可以为空）：400
      - 未找到文件：404
      - 成功：200
    - docker_create_file、docker_create_folder：201 if success else 500
    - docker_delete_file、docker_delete_folder、docker_rename_file：200 if success else 500
    - docker_get_pip_list: 200 if success else 500
    - docker_add_python_package、docker_add_nodejs_package: 201 if success else 500
    - docker_delete_python_package、docker_delete_nodejs_package：200 if success else 500
