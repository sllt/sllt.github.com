title: 实现网打算换成puma来跑
date: 2015-01-20 16:25:43
tags: rails
---
将unicorn换成puma的原因：
* 节省内存 ，提高效率
* Capistrano部署集成（capistrano3-puma）

以下为手动配置方法：
启动puma
```
bundle exec puma -b unix:///tmp/puma.sock -e production --daemon
```
nginx配置例子：
​
```
upstream shixian {
  server unix:///tmp/puma.sock;
}

server {
  listen 80;
  server_name dev.shixian.com;

  # ~2 seconds is often enough for most folks to parse HTML/CSS and
  # retrieve needed images/icons/frames, connections are cheap in
  # nginx so increasing this is generally safe...
  keepalive_timeout 5;

  # path for static files
  root /home/deploy/apps/shixian/public;
  access_log /home/deploy/apps/shixian/log/nginx.access.log;
  error_log /home/deploy/apps/shixian/log/nginx.error.log info;

  # this rewrites all the requests to the maintenance.html
  # page if it exists in the doc root. This is for capistrano's
  # disable web task
  if (-f $document_root/maintenance.html) {
    rewrite  ^(.*)$  /maintenance.html last;
    break;
  }

  location / {
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;

    # If the file exists as a static file serve it directly without
    # running all the other rewite tests on it
    if (-f $request_filename) {
      break;
    }

    # check for index.html for directory index
    # if its there on the filesystem then rewite
    # the url to add /index.html to the end of it
    # and then break to send it to the next config rules.
    if (-f $request_filename/index.html) {
      rewrite (.*) $1/index.html break;
    }

    # this is the meat of the rack page caching config
    # it adds .html to the end of the url and then checks
    # the filesystem for that file. If it exists, then we
    # rewite the url to have explicit .html on the end
    # and then send it on its way to the next config rule.
    # if there is no file on the fs then it sets all the
    # necessary headers and proxies to our upstream pumas
    if (-f $request_filename.html) {
      rewrite (.*) $1.html break;
    }

    if (!-f $request_filename) {
      proxy_pass http://shixian;
      break;
    }
  }

  # Now this supposedly should work as it gets the filenames with querystrings that Rails provides.
  # BUT there's a chance it could break the ajax calls.
  location ~* \.(ico|css|gif|jpe?g|png|js)(\?[0-9]+)?$ {
     expires max;
     break;
  }

  # Error pages
  # error_page 500 502 503 504 /500.html;
  location = /500.html {
    root /home/deploy/apps/shixian/public;
  }
}
```
