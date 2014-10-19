# Baiduyun Cli

这是一个用 `python-request` 写的命令行下的百度云网盘客户端  
API来源于网页js与抓包

**这个项目尚未完成**

## Usage

```shell
python main.py login
python main.py download
```
注意到下载功能依赖于`Aria2`
在运行这个脚本前，请先到下载到的目录下运行
```
aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all -c
```
以后会加入其他后端的支持

## P&Q

这个项目应该不会有Fork的吧……