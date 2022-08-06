# login接口说明
## is_login

### 接口地址
127.0.0.1:5000/login/is_login/
### Method
GET  
### 接口说明
is_login用于判断当前登录状态，通过sessions中是否含有'username'项进行判断，若是则返回对应的username，若否返回False。
## login
### 接口地址
127.0.0.1:5000/login/login/
### Method
GET，POST
### 接口说明
login用于登录。  

&ensp;&ensp;&ensp;&ensp;当以GET方式请求时，返回通过render_template函数渲染指定路径下对应的模板文件login.html。  

&ensp;&ensp;&ensp;&ensp;当以POST方式请求时，请求体里需要带上一个由username参数和password参数以及值为"{{ csrf_token() }}"的csrf_token组成的form（具体可以参见backend/templates/login.html）。  

&ensp;&ensp;&ensp;&ensp;之后后端会调用数据库查询操作对登录信息进行检测，若成功登录则重定向到index界面（127.0.0.1:5000/login/）  

&ensp;&ensp;&ensp;&ensp;后续可以根据需要修改重定向后的地址及渲染模板html。
## logout
### 接口地址
127.0.0.1:5000/login/logout/
### Method
GET
### 接口说明
访问该接口将登出当前用户并重定向到登录界面。
## register
### 接口地址
127.0.0.1:5000/login/register/
### Method
GET，POST
### 接口说明
该接口用于注册。  

&ensp;&ensp;&ensp;&ensp;与login接口类似，当请求方式为GET时，返回渲染的模板register.html  

&ensp;&ensp;&ensp;&ensp;当以POST方式请求时，请求体里需要带上一个由username参数和password参数和password_confirm参数以及值为"{{ csrf_token() }}"的csrf_token组成的form  

&ensp;&ensp;&ensp;&ensp;之后后端会对参数合法性进行验证，若通过，则将用户名及密码保存到数据库，并重定向回登录界面。
## deregister
### 接口地址
127.0.0.1:5000/login/deregister/
### Method
GET，POST
### 接口说明
该接口用于注销账号  

&ensp;&ensp;&ensp;&ensp;与前面的接口类似，当请求方式为GET时，返回渲染的模板deregister.html。  

&ensp;&ensp;&ensp;&ensp;当请求方式为POST时，请求体里需要带上一个由username参数和password参数以及值为"{{ csrf_token() }}"的csrf_token组成的form  

&ensp;&ensp;&ensp;&ensp;之后后端会调用数据库操作对参数进行验证，若验证通过，则将账户从数据库中删除，并重定向到登录界面。
