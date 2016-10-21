title: 如何写一个web服务器
date: 2015-11-25 16:14:41
tags: [python, server]
---

Hello, Web

我们先来写一个简单的web服务器，思路如下：

1. 等待客户端连接我们的服务器，并发送一个HTTP 请求；
2. 解析这个请求；
3. 找出它要请求的具体内容；
4. 获取该数据 (或者动态生成);
5. 将数据格式化为HTML；
6. 返回数据。

步骤1、2、6的实现方式大致相同, 在Python中有一个叫BaseHTTPServer的模块可以帮助我们实现这些步骤。 我们仅需要实现步骤3-5, 一个简单的实现如下:

    import BaseHTTPServer
    
    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        '''Handle HTTP requests by returning a fixed 'page'.'''
    
        # Page to send back.
        Page = '''\
    <html>
    <body>
    <p>Hello, web!</p>
    </body>
    </html>
    '''
    
        # Handle a GET request.
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(self.Page)))
            self.end_headers()
            self.wfile.write(self.Page)
    
    #----------------------------------------------------------------------
    
    if __name__ == '__main__':
        serverAddress = ('', 8080)
        server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
        server.serve_forever()

BaseHTTPRequestHandler类负责解析传入的HTTP请求， 并调用特定的方法。如果是GET请求，它将调用do_GET方法。我们的RequestHandler类重写了这个方法来动态的生成一个页面：返回的内容保存在类变量Page中，我们给客户端返回一个200的状态码，Content-Type用来告诉客户端将我们返回的数据为HTML，Content-Length表示返回信息的长度（end_headers方法将会插入空行用来分割HTTP头以及内容主体）。

但RequestHandler并不是故事的全部：我们需要调用最后三行代码来启动一个服务器。其中第一行定义了一个元组来表示服务器的地址：空字符串表示“运行在当前的机器上”，8080表示占用的端口。接着我们创建了一个BaseHTTPServer.HTTPServer的实例，然后让其一直运行（按Control-C终止）。

我们在命令行下运行这个程序， 并不会显示任何内容：

    $ python server.py

用浏览器打开 http://localhost:8080 我们会看到以下内容：

    Hello, web!

这时候我们的shell将会显示类似如下信息：

    127.0.0.1 - - [24/Feb/2014 10:26:28] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [24/Feb/2014 10:26:28] "GET /favicon.ico HTTP/1.1" 200 -

因为我们没有指定特定的文件，浏览器默认将会访问'/'目录（服务器的根目录）。

浏览器会自动发送第二个请求获取/favicon.ico图像,它会显示在地址栏上，如果它存在的话。

Displaying Values

我们来修改代码让程序返回HTTP请求的部分信息 。 为了保持代码的整洁，我们将分为几个方法来写：

    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
        # ...page template...
    
        def do_GET(self):
            page = self.create_page()
            self.send_page(page)
    
        def create_page(self):
            # ...fill in...
    
        def send_page(self, page):
            # ...fill in...



我们需要先实现send_page方法： 

    def send_page(self, page):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

将要显示的页面模板：

        Page = '''\
    <html>
    <body>
    <table>
    <tr>  <td>Header</td>         <td>Value</td>          </tr>
    <tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
    <tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
    <tr>  <td>Client port</td>    <td>{client_port}s</td> </tr>
    <tr>  <td>Command</td>        <td>{command}</td>      </tr>
    <tr>  <td>Path</td>           <td>{path}</td>         </tr>
    </table>
    </body>
    </html>
    '''

实现create_page方法，用来格式化要显示的信息：

    def create_page(self):
        values = {
            'date_time'   : self.date_time_string(),
            'client_host' : self.client_address[0],
            'client_port' : self.client_address[1],
            'command'     : self.command,
            'path'        : self.path
        }
        page = self.Page.format(**values)
        return page



不需要改变程序主体: 像之前一样, 以地址、RequestHandler作为参数创建一个 HTTPServer的实例，接着程序会监听此地址。如果我们用浏览器打开http://localhost:8080/something.html，将会看到如下信息：  

      Date and time  Mon, 24 Feb 2014 17:17:12 GMT
      Client host    127.0.0.1
      Client port    54548
      Command        GET
      Path           /something.html

即使something.html页面不存在程序也不会返回一个404错误。这是因为我们在获取一个HTTP请求后可以给它返回任意内容。

Serving Static Pages

接下来我们监听磁盘上的文件，将其返回给客户端。来修改do_GET方法:

    def do_GET(self):
        try:
    
            # Figure out what exactly is being requested.
            full_path = os.getcwd() + self.path
    
            # It doesn't exist...
            if not os.path.exists(full_path):
                raise ServerException("'{0}' not found".format(self.path))
    
            # ...it's a file...
            elif os.path.isfile(full_path):
                self.handle_file(full_path)
    
            # ...it's something we don't handle.
            else:
                raise ServerException("Unknown object '{0}'".format(self.path))
    
        # Handle errors.
        except Exception as msg:
            self.handle_error(msg)
    



该方法假定服务器所在目录为根目录(调用 os.getcwd方法)。然后跟URL中的地址组合在一起来寻找文件 (相对路径保存在 self.path中，并始终以'/'开头) 。

如果这个文件不存在，或者不是个文件程序会抛出一个异常，并捕获它。如果这个文件存在，将会调用hand_file方法来获取文件的内容。然后调用send_content方法将读到的内容返回给客户端：

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(msg)



接着，我们来完成错误处理的方法和错误报告的页面模板：

    Error_Page = """\
            <html>
            <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
            """
    
    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content)

This program works, but only if we don't look too closely. The problem is that it always returns a status code of 200, even when the page being requested doesn't exist. Yes, the page sent back in that case contains an error message, but since our browser can't read English, it doesn't know that the request actually failed. In order to make that clear, we need to modify handle_error and send_content as follows:

    # Handle unknown objects.
    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)
    
    # Send actual content.
    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)



Listing Directories

As our next step, we could teach the web server to display a listing of a directory's contents when the path in the URL is a directory rather than a file. We could even go one step further and have it look in that directory for an index.html file to display, and only show a listing of the directory's contents if that file is not present.

But building these rules into do_GET would be a mistake, since the resulting method would be a long tangle of if statements controlling special behaviors. The right solution is to step back and solve the general problem, which is figuring out what to do with a URL. Here's a rewrite of the do_GET method:

    def do_GET(self):
        try:
    
            # Figure out what exactly is being requested.
            self.full_path = os.getcwd() + self.path
    
            # Figure out how to handle it.
            for case in self.Cases:
                handler = case()
                if handler.test(self):
                    handler.act(self)
                    break
    
        # Handle errors.
        except Exception as msg:
            self.handle_error(msg)



The first step is the same: figure out the full path to the thing being requested. After that, though, the code looks quite different. Instead of a bunch of inline tests, this version loops over a set of cases stored in a list. Each case is an object with two methods: test, which tells us whether it's able to handle the request, and act, which actually takes some action. As soon as we find the right case, we let it handle the request and break out of the loop.

These three case classes reproduce the behavior of our previous server:



    class case_no_file(object):
        '''File or directory does not exist.'''
    
        def test(self, handler):
            return not os.path.exists(handler.full_path)
    
        def act(self, handler):
            raise ServerException("'{0}' not found".format(handler.path))
    
    
    class case_existing_file(object):
        '''File exists.'''
    
        def test(self, handler):
            return os.path.isfile(handler.full_path)
    
        def act(self, handler):
            handler.handle_file(handler.full_path)
    
    
    class case_always_fail(object):
        '''Base case if nothing else worked.'''
    
        def test(self, handler):
            return True
    
        def act(self, handler):
            raise ServerException("Unknown object '{0}'".format(handler.path))

and here's how we construct the list of case handlers at the top of the RequestHandler class:

    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        '''
        If the requested path maps to a file, that file is served.
        If anything goes wrong, an error page is constructed.
        '''
    
        Cases = [case_no_file(),
                 case_existing_file(),
                 case_always_fail()]
    
        ...everything else as before...

Now, on the surface this has made our server more complicated, not less: the file has grown from 74 lines to 99, and there's an extra level of indirection without any new functionality. The benefit comes when we go back to the task that started this chapter and try to teach our server to serve up the index.html page for a directory if there is one, and a listing of the directory if there isn't. The handler for the former is:

    class case_directory_index_file(object):
        '''Serve index.html page for a directory.'''
    
        def index_path(self, handler):
            return os.path.join(handler.full_path, 'index.html')
    
        def test(self, handler):
            return os.path.isdir(handler.full_path) and \
                   os.path.isfile(self.index_path(handler))
    
        def act(self, handler):
            handler.handle_file(self.index_path(handler))
    

Here, the helper method index_path constructs the path to the index.html file; putting it in the case handler prevents clutter in the main RequestHandler.test checks whether the path is a directory containing an index.html page, and act asks the main request handler to serve that page.

The only change needed to RequestHandler is to add a case_directory_index_file object to our Cases list:

        Cases = [case_no_file(),
                 case_existing_file(),
                 case_directory_index_file(),
                 case_always_fail()]

What about directories that don't contain index.html pages? The test is the same as the one above with a not strategically inserted, but what about the actmethod? What should it do?

    class case_directory_no_index_file(object):
        '''Serve listing for a directory without an index.html page.'''
    
        def index_path(self, handler):
            return os.path.join(handler.full_path, 'index.html')
    
        def test(self, handler):
            return os.path.isdir(handler.full_path) and \
                   not os.path.isfile(self.index_path(handler))
    
        def act(self, handler):
            ???

It seems we've backed ourselves into a corner. Logically, the act method should create and return the directory listing, but our existing code doesn't allow for that:RequestHandler.do_GET calls act, but doesn't expect or handle a return value from it. For now, let's add a method to RequestHandler to generate a directory listing, and call that from the case handler's act:

    class case_directory_no_index_file(object):
        '''Serve listing for a directory without an index.html page.'''
    
        # ...index_path and test as above...
    
        def act(self, handler):
            handler.list_dir(handler.full_path)
    
    
    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
        # ...all the other code...
    
        # How to display a directory listing.
        Listing_Page = '''\
            <html>
            <body>
            <ul>
            {0}
            </ul>
            </body>
            </html>
            '''
    
        def list_dir(self, full_path):
            try:
                entries = os.listdir(full_path)
                bullets = ['<li>{0}</li>'.format(e) 
                    for e in entries if not e.startswith('.')]
                page = self.Listing_Page.format('\n'.join(bullets))
                self.send_content(page)
            except OSError as msg:
                msg = "'{0}' cannot be listed: {1}".format(self.path, msg)
                self.handle_error(msg)
    

The CGI Protocol

Of course, most people won't want to edit the source of their web server in order to add new functionality. To save them from having to do so, servers have always supported a mechanism called the Common Gateway Interface (CGI), which provides a standard way for a web server to run an external program in order to satisfy a request.

For example, suppose we want the server to be able to display the local time in an HTML page. We can do this in a standalone program with just a few lines of code:

    from datetime import datetime
    print '''\
    <html>
    <body>
    <p>Generated {0}</p>
    </body>
    </html>'''.format(datetime.now())

In order to get the web server to run this program for us, we add this case handler:

    class case_cgi_file(object):
        '''Something runnable.'''
    
        def test(self, handler):
            return os.path.isfile(handler.full_path) and \
                   handler.full_path.endswith('.py')
    
        def act(self, handler):
            handler.run_cgi(handler.full_path)

The test is simple: does the file path end with .py? If so, RequestHandler runs this program.

        def run_cgi(self, full_path):
            cmd = "python " + full_path
            child_stdin, child_stdout = os.popen2(cmd)
            child_stdin.close()
            data = child_stdout.read()
            child_stdout.close()
            self.send_content(data)

This is horribly insecure: if someone knows the path to a Python file on our server, we're just letting them run it without worrying about what data it has access to, whether it might contain an infinite loop, or anything else.2

Sweeping that aside, the core idea is simple:

1. Run the program in a subprocess.
2. Capture whatever that subprocess sends to standard output.
3. Send that back to the client that made the request.

The full CGI protocol is much richer than this—in particular, it allows for parameters in the URL, which the server passes into the program being run—but those details don't affect the overall architecture of the system...

...which is once again becoming rather tangled. RequestHandler initially had one method, handle_file, for dealing with content. We have now added two special cases in the form of list_dir and run_cgi. These three methods don't really belong where they are, since they're primarily used by others.

The fix is straightforward: create a parent class for all our case handlers, and move other methods to that class if (and only if) they are shared by two or more handlers. When we're done, the RequestHandler class looks like this:

    class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
        Cases = [case_no_file(),
                 case_cgi_file(),
                 case_existing_file(),
                 case_directory_index_file(),
                 case_directory_no_index_file(),
                 case_always_fail()]
    
        # How to display an error.
        Error_Page = """\
            <html>
            <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
            """
    
        # Classify and handle request.
        def do_GET(self):
            try:
    
                # Figure out what exactly is being requested.
                self.full_path = os.getcwd() + self.path
    
                # Figure out how to handle it.
                for case in self.Cases:
                    if case.test(self):
                        case.act(self)
                        break
    
            # Handle errors.
            except Exception as msg:
                self.handle_error(msg)
    
        # Handle unknown objects.
        def handle_error(self, msg):
            content = self.Error_Page.format(path=self.path, msg=msg)
            self.send_content(content, 404)
    
        # Send actual content.
        def send_content(self, content, status=200):
            self.send_response(status)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
    

while the parent class for our case handlers is:

    class base_case(object):
        '''Parent for case handlers.'''
    
        def handle_file(self, handler, full_path):
            try:
                with open(full_path, 'rb') as reader:
                    content = reader.read()
                handler.send_content(content)
            except IOError as msg:
                msg = "'{0}' cannot be read: {1}".format(full_path, msg)
                handler.handle_error(msg)
    
        def index_path(self, handler):
            return os.path.join(handler.full_path, 'index.html')
    
        def test(self, handler):
            assert False, 'Not implemented.'
    
        def act(self, handler):
            assert False, 'Not implemented.'

and the handler for an existing file (just to pick an example at random) is:

    class case_existing_file(base_case):
        '''File exists.'''
    
        def test(self, handler):
            return os.path.isfile(handler.full_path)
    
        def act(self, handler):
            self.handle_file(handler, handler.full_path)

Discussion

The differences between our original code and the refactored version reflect two important ideas. The first is to think of a class as a collection of related services.RequestHandler and base_case don't make decisions or take actions; they provide tools that other classes can use to do those things.

The second is extensibility: people can add new functionality to our web server either by writing an external CGI program, or by adding a case handler class. The latter does require a one-line change to RequestHandler (to insert the case handler in the Cases list), but we could get rid of that by having the web server read a configuration file and load handler classes from that. In both cases, they can ignore most lower-level details, just as the authors of the BaseHTTPRequestHandlerclass have allowed us to ignore the details of handling socket connections and parsing HTTP requests.

These ideas are generally useful; see if you can find ways to use them in your own projects.


