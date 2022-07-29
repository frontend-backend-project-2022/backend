### **注意**：请在linux环境下运行，`pty, select`模块在Windows下不能正常工作

* `flask run`启动应用

* 或是用`python app.py`以调试模式启动应用

* 可以更改`views`下的文件，`views/{module}.py`的API将放在`localhost:5000/{module}`前缀下（具体参见`app.py`中的`app.register_blueprint`语句）。

* 例如访问`localhost:5000/docker/`可以看到`docker`模块的API

如果安装了新的库记得更新`requirements.txt`，有什么进展也可以写在`README`里。
