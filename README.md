### **注意**：请在 linux 环境下运行，`pty, select`模块在 Windows 下不能正常工作

- `flask run`启动应用

- 或是用`python app.py`以调试模式启动应用

- 可以更改`views`下的文件，`views/{module}.py`的 API 将放在`localhost:5000/{module}`前缀下（具体参见`app.py`中的`app.register_blueprint`语句）。

- 例如访问`localhost:5000/docker/`可以看到`docker`模块的 API

- Xterm.js Demo 连接的 Docker Container 根据的是 username 对应的 container.id

  - `["docker", "exec", "-it", containerid, "bash"]`(详见 app.py)

  - username 目前硬编码为前端\src\views\TerminalView.vue 内的"Dave"。如果该用户名曾经访问过 ternimal，则读取上次的 container；否则创建一个新 container 且 name 设定为 username

- docker 安装详见[菜鸟教程](https://www.runoob.com/docker/ubuntu-docker-install.html)

- database 采用 sqlite3，用户表名称为 USER，形式如下:

  - ```sqlite
    USER(
        id INTEGER AUTO_INCREMENT,
        name TEXT NOT NULL UNIQUE,
        pwhash TEXT NOT NULL,
        container_id TEXT NOT NULL,
        PRIMARY KEY (id)
    )
    ```

  - 注：pwhash 是 password 经过 sha256 加盐 hash 得到的

  - API:

    - db_insert(name, pw)可直接插入新 user（包括建立 container）

    - db_select(name)通过 name 获取(name, pwhash, container_id) 三元组

    - db_verify_pw(name, pw)输入 name 和 password 返回二者是否对应(True/False)

    - db_delete(name, pw)输入 name 和 password，如果二者匹配成功则删除，返回删除是否成功(True/False)

如果安装了新的库记得更新`requirements.txt`，有什么进展也可以写在`README`里。

7/30（徐浩博）：docker.py 给出了在 docker 内执行某个 bash 操作的 api，正确性有待测试

-login.py 实现了index，login，register，deregister四个页面的跳转，其中只简单实现了四个网页，并放在backend目录下的templates目录里。在login.py中使用rander_template函数渲染网页。

  -访问127.0.0.1:5000/login/ 若已登录，则显示index.html欢迎界面；若未登录，则重定向至登录界面127.0.0.1:5000/login/login/
  
  -用户需要先点击登录界面的register按钮注册，输入4-64位的用户名，8-64位的密码，并再次输入相同密码才能完成注册，注册成功后会自动跳转回登录界面
  
  -用户登录成功后会跳转到127.0.0.1:5000/login/ 登录成功后可以点击该页面的logout链接登出。
  
  -用户可以点击login界面的deregister链接进入账号注销界面127.0.0.1:5000/login/deregister 正确输入用户名和密码并确认后账号将注销。
  
  -接口is_login()当用户已登录时返回True，否则返回False。

-form.py 规定了register、deregister、login的form格式，对用户名和密码的长度做了一定限制。之后也可以考虑引入正则表达式对其添加其他内容上的限制。
