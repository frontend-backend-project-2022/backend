### **注意**：请在linux环境下运行，`pty, select`模块在Windows下不能正常工作

* `flask run`启动应用

* 或是用`python app.py`以调试模式启动应用

* 可以更改`views`下的文件，`views/{module}.py`的API将放在`localhost:5000/{module}`前缀下（具体参见`app.py`中的`app.register_blueprint`语句）。

* 例如访问`localhost:5000/docker/`可以看到`docker`模块的API

* 目前Xterm.js Demo连接的Docker Container是硬编码在`app.py`里的
  
  * `["docker", "exec", "-it", "6a8", "bash"]`
  
  * 可以先在命令行里运行`docker run -d ubuntu tail -f /dev/null`，创建一个不停止的Container，然后记下Container的ID，把`6a8`替换成新的ID即可。

如果安装了新的库记得更新`requirements.txt`，有什么进展也可以写在`README`里。