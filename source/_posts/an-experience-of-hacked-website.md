---
title: 一次误打误撞的提权经历
date: 2016-11-09 15:02:21
tags: "webshell"
---

误打误撞的输入某网站的ip结果自动跳转到一个探针文件：

![](http://o73uhz20r.bkt.clouddn.com/an-experience-of-hacked-website-1.png)

通过弱口令尝试登录数据库，测试成功！

phpstudy这种集成包一般也会集成phpMyAdmin， 尝试找phpMyAdmin的相对路径登录，成功登录后通过select outfile语句将一句话木马写入到web服务器根目录下（探针暴露了绝对路径）

![](http://o73uhz20r.bkt.clouddn.com/an-experience-of-hacked-website-2.png)


测试是否写入成功

![](http://o73uhz20r.bkt.clouddn.com/an-experience-of-hacked-website-3.png)

通过第三方工具连接一句话木马上传GetPassword.exe 并运行。

![](http://o73uhz20r.bkt.clouddn.com/an-experience-of-hacked-website-4.png)



成功拿到密码

![](http://o73uhz20r.bkt.clouddn.com/an-experience-of-hacked-website-5.png)