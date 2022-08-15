## Bpan
[![PyPI version](https://img.shields.io/pypi/v/bpan.svg?logo=pypi&logoColor=FFE873)](https://pypi.python.org/pypi/bpan)

`Bpan`是用于命令行管理用户百度网盘文件的`api`，用户授权登录百度网盘账户，获取授权`Token`，使用`Token`认证，实现百度网盘账户基础信息访问和百度网盘管理权限。



### 1. 依赖

##### 1.1 运行环境：

+ linux64
+ python>=3.7

##### 1.2 其他python模块依赖：

+ Cython
+ requests
+ requests-toolbelt
+ tqdm
+ urllib3
+ prettytable



### 2. 特性

+ `Bpan`软件使用百度网盘开放平台提供的接口，封装了相关使用的`http`请求实现个人百度网盘数据管理
+ 目前版本为`1.0.0`， 暂时仅支持登录，退出，查看文件，查看网盘账户信息，下载功能
+ 增加了并行多文件下载，断点续传，以及下载完成后的md5自动校验功能
+ 可直接将网盘文件下载到本地指定路径



### 3. 安装

> git仓库安装：

```
pip3 install git+https://github.com/yodeng/bpan.git
```

> Pypi官方源安装：

```
pip3 install bpan==1.0.0
```



### 4. 使用

相关命令使用`-h/--help`查看命令帮助参数

##### 4.1 登录

登录使用`bpan login`命令，登录成功后运行命令无需再次登录。

![login](https://user-images.githubusercontent.com/18365846/183331921-356c5e0a-0416-4f91-bd1e-f9a12f04785a.png)

会提示登录网址，浏览器打开网址，即可进入`Bpan`登录界面，输入百度网盘账户名和密码，获取授权码，授权码10分钟内有效。

将授权码复制到命令行提示位置，即可完成授权登录，登录后会输出百度网盘账户基础信息，代表登录成功。

![log_success](https://user-images.githubusercontent.com/18365846/183331918-db3e7d1b-3c63-4467-adc8-b8347dfc7562.png)

登录成功后，百度网盘`"我的应用数据/"`目录下会创建一个子文件夹`"Bpan/"`，该目录为`Bpan`软件的根目录，保存到此目录下的目录即可通过`bpan`命令进行查看下载。

##### 4.2 退出登录

退出登录使用`bpan logout`命令，退出登录之后，使用命令会提示未登录，要运行需要重新登录。

![logout](https://user-images.githubusercontent.com/18365846/183331925-d5670ea2-cabc-43bf-97d4-05bbd2b61171.png)



##### 4.3 查看文件

查看文件使用`bpan ls`或`bpan list`命令， 默认查看根目录下的文件。 `Bpan`软件根目录对应百度网盘的`"我的应用数据/Bpan/"`目录。

![list](https://user-images.githubusercontent.com/18365846/183331930-f673328a-b3c8-4c33-bdaf-c5a414ef6b42.png)

+ 蓝色显示为文件夹，白色显示为文件
+ `path`路径为`Bpan`软件使用的路径，对应百度网盘实际存储目录为`"/我的应用数据/Bpan/"`
+ `size`表示文件大小，目录为"-"
+ `md5`表示文件的`md5`值，目录为"-"
+ `bpan ls [path]` 可查看指定`path`的文件或目录



##### 4.4 查看网盘账户信息

查看网盘账户信息使用 `bpan info`命令

![info](https://user-images.githubusercontent.com/18365846/183331928-e2eb98cc-e95d-4680-8d82-db4773969c01.png)

会输出已登录的百度网盘账户名，是否是vip信息，总空间，已使用空间信息

##### 4.5 文件下载

文件下载使用`bpan download`命令，只允许下载`"/我的应用数据/Bpan/"`下的文件或者目录，其他位置的文件需要在百度网盘客户端将文件转移到`"/我的应用数据/Bpan/"`目录下才能下载。

下载采用`asyncio`异步，支持多文件同时并行下载，支持断点续传。

```shell
$ bpan download -h
usage: bpan download [-h] [-v] -i <file/dir> -o <dir> [-t <int>] download

download file or directory from netdisk to local directory.

optional arguments:
  -h, --help            show this help message and exit

General options:
  download
  -v, --version         show program's version number and exit

Options:
  -i <file/dir>, --input <file/dir>
                        input file or directory of remote path to download, required
  -o <dir>, --outdir <dir>
                        local directory for download, it will be create if not exists. required
  -t <int>, --threads <int>
                        which number of file for download in parallel, default 1
```

参数说明如下：

| 参数         | 描述                                                         |
| ------------ | ------------------------------------------------------------ |
| -i/--input   | 要下载的文件或者目录，根目录代表实际网盘的`"/我的应用数据/Bpan/"`目录 |
| -o/--outdir  | 保存到本地的输出目录，不存在会自动创建                       |
| -t/--threads | 运行同时下载的文件个数，默认1个                              |
| -v/--version | 打印bpan版本并退出                                           |
| -h/--help    | 打印软件帮助并退出                                           |

![download](https://user-images.githubusercontent.com/18365846/183331927-25746071-a654-4274-b78c-c88a0783083c.png)



### 5. 说明

+ 下载网速根据网络和账户决定，百度网盘对于非会员账户做了限速，最大速度`100~200kb/s`，对于会员账户，`bpan`下载速度能达到`10M/s`以上



### 6. 参考

[https://pan.baidu.com/union](https://pan.baidu.com/union)
