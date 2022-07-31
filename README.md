### **注意**：请在linux环境下运行，`pty, select`模块在Windows下不能正常工作

* `flask run`启动应用

* 或是用`python app.py`以调试模式启动应用

* 可以更改`views`下的文件，`views/{module}.py`的API将放在`localhost:5000/{module}`前缀下（具体参见`app.py`中的`app.register_blueprint`语句）。

* 例如访问`localhost:5000/docker/`可以看到`docker`模块的API

* Xterm.js Demo连接的Docker Container根据的是username对应的container.id
  
  * `["docker", "exec", "-it", containerid, "bash"]`(详见app.py)
  
  * username目前硬编码为前端\src\views\TerminalView.vue内的"Dave"。如果该用户名曾经访问过ternimal，则读取上次的container；否则创建一个新container且name设定为username
  
* docker安装详见[菜鸟教程](https://www.runoob.com/docker/ubuntu-docker-install.html)

* database采用sqlite3，用户表名称为USER，形式如下:

  * ```sqlite
    USER(
        id INTEGER AUTO_INCREMENT, 
        name TEXT NOT NULL, 
        pwhash TEXT NOT NULL,
        container_id TEXT NOT NULL,
        PRIMARY KEY (id)
    )
    ```

  * 注：pwhash是password经过sha256加盐hash得到的

  * API: 

    * db_insert(name, pw)可直接插入新user（包括建立container）

    * db_select(name)通过name获取(name, pwhash, container_id) 三元组

    * db_verify_pw(name, pw)输入name和password返回二者是否对应(True/False)

      


如果安装了新的库记得更新`requirements.txt`，有什么进展也可以写在`README`里。



7/30（徐浩博）：docker.py给出了在docker内执行某个bash操作的api，正确性有待测试
