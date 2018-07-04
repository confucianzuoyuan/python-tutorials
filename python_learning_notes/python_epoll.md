# Blocking Socket Programming Examples

阻塞的socket编程举例

```py
import socket

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(1)

connectionclient, address = serversocket.accept()
request = b''
while EOL1 not in request and EOL2 not in request:
    request += connectionclient.recv(1024)
print(request.decode())
connectionclient.send(response)
connectionclient.close()

serversocket.close()
```

下面的代码中增加了一个循环，可以重复地处理客户端连接，直到被用户中断。这个例子清楚地表明server这个socket并不与客户端交换数据，它只是接收来自客户端的连接，然后在server机上创建一个新的socket，然后是这个新的socket与客户端沟通。

```py
import socket

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(1) # backlog为1

try:
    while True:
        connectionclient, address = serversocket.accept()
        request = b''
        while EOL1 not in request and EOL2 not in request:
            request += connectionclient.recv(1024)
        print('-' * 40 + '\n' + request.decode()[:-2])
        connectionclient.send(response)
        connectionclient.close()
finally:
    serversocket.close()
```

# Benefits of Asynchronous Sockets and Linux epoll

上例中展示的socket称为阻塞socket，因为程序直到事件发生才停止运行。`accept()`函数会一直阻塞，直到有来自客户端的连接；`recv()`函数会一直阻塞，直到接收到了客户端的数据（或者没有更多的可接收数据）；`send()`函数也会一直阻塞，直到发送给客户端的数据已经准备好了。

通常来说，阻塞socket程序会用一个线程（或进程）来处理来自一个客户端连接产生的socket。程序主线程包含了监听socket，这个监听socket接受来自众多客户端的连接；每当一个客户端连接进来时，将新创建的socket交给另外一个线程，由这个线程与客户端进行通信。因为每个线程只会与一个客户端通信，因此一个线程的阻塞并不会影响其它工作线程。

使用多线程的阻塞socket写的代码逻辑上很简单直接，但这种模型有一些缺点，比如多线程的数据同步和单CPU多线程的低效。

C10K问题讨论了处理并发的一些策略，其中包括异步socket。对异步socket的操作会立即返回成功或失败，程序可以通过返回来决定后续操作。因为异步socket是非阻塞的，所以不需要用多线程，所有任务可能都在一个线程中完成。这种异步单线程模型也有自身的问题，但对大多数场景来说已经足够了。当然，可以使用异步多线程模型：主线程负责网络处理，其它线程用户获取阻塞资源（例如DB).

Linux有一些异步socket的管理机制，Python提供了`select、poll、epoll`三个API。`epoll`和`poll`比`select`更高效，因为select需要用户程序对每一个socket的事件进行检查，而另外两个则可以依赖操作系统来获知哪些socket正在发生指定的事件。另外，相较于poll，epoll更好，因为它不需要操作系统检查所有的socket来获知事件；当事件发生时，操作系统会追踪这些事件，在应用程序查询的时候，操作系统会返回一个列表。

# Asynchronous Socket Programming Examples with epoll

使用epoll的程序通常会执行以下步骤：
- 创建一个epoll对象
- 让epoll对象监听指定sockets上的指定事件
- 告诉epoll对象自最后一次查询后哪些sockets上可能发生了指定事件
- 在这些sockets上执行一些动作
- 让epoll对象修改一列sockets和/或需要监听的事件
- 重复3~5直至完成
- 销毁epoll对象

下面的程序利用异步socket完成了上例的功能:

```py
import socket
import select  #: epoll包含在select模块中

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(1)
serversocket.setblocking(0)  #: 默认情况下，socket处于阻塞模式

epoll = select.epoll()       #: 创建一个epoll对象
# 在serversocket上注册读事件，读事件发生在serversocket每次接受socket连接时
epoll.register(serversocket.fileno(), select.EPOLLIN)

try:
    # 文件描述符（整数）与其对应的网络连接对象的映射
    connections = {}
    requests = {}
    responses = {}
    while True:
        # 查询epoll对象，看是否有感兴趣的事件发生
        # 参数`1`表明我们最多会等待1秒钟
        # 如果在这次查询之前有我们感兴趣的事件发生，这次查询将会立即返回这些事件的列表
        events = epoll.poll(1)
        # 事件是一个`(fileno, 事件code)`的元组
        for fileno, event in events:
            # 如果serversocket上发生了读事件，那么意味着有一个有新的连接
            if fileno == serversocket.fileno():
                connection, address = serversocket.accept()
                # 将新的socket设为非阻塞
                connection.setblocking(0)
                # 给新创建的socket注册读事件（EPOLLIN），表明将有数据请求
                epoll.register(connection.fileno(), select.EPOLLIN)
                connections[connection.fileno()] = connection
                # 收集各客户端来的请求
                requests[connection.fileno()] = b''
                responses[connection.fileno()] = response
            elif event & select.EPOLLIN:
                # 如果发生了读事件，从客户端读取数据
                requests[fileno] += connections[fileno].recv(1024)
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    # 一旦请求被完全接收了，注销这个socket的读事件，然后注册写事件（EPOLLOUT）
                    # 表明响应即将开始
                    # 当向客户端发送响应的时候，读事件发生
                    epoll.modify(fileno, select.EPOLLOUT)
                    # 打印出完整的请求
                    # 结果表明：尽管客户端请求交错发生，每一个客户端的请求仍然能被聚合起来
                    print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            elif event & select.EPOLLOUT:
                # 如果发生了写事件，向客户端发送响应
                # 每次向客户端发送一定长度的响应内容，每次都更新余下待发送的响应内容
                byteswritten = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][byteswritten:]
                # 响应已经发送完毕，一次请求/响应周期完成，不再监听该socket的事件了
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, 0)
                # 告诉客户端，关闭连接
                connections[fileno].shutdown(socket.SHUT_RDWR)
            # `HUP`（挂起）事件表明客户端断开了连接
            elif event & select.EPOLLHUP:
                # 注销对断开客户端socket的事件监听
                epoll.unregister(fileno)
                # 关闭连接，服务端关闭
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()
```

`epoll`有两种操作模式，`edge-triggered`和`level-triggerd`。`epoll`默认水平触发工作模式。

# 关于ET和LT

当一个fd准备好读写时，我们可能不需要立即读出（或写入）所有的数据。

当fd准备好时，LT会不停地告诉你这个fd准备好了；而ET不会这样，它会告诉你一次，然后直到下一次遇到EAGAIN。因此，ET模式的代码有时会略复杂，但是却更高效。

假设你要将数据写入某个使用LT模式注册读事件的fd，你将会持续接收到这个fd可读的通知，如果待写入的数据尚未准备好，那么这种模式会浪费资源，因为即使得到这一通知，你也无法写入数据。

如果你使用的是ET模式，你只会收到一次这个fd可写的通知，然后当数据准备好了你可以尽可能多的写入，如果此时write(2)返回EAGAIN，写入会停止，等到下次通知时再行写入。

读过程同理，因为有时在尚未准备好时，你可能不希望将所有数据一次性读入到用户空间。

# Edge Triggered

假设有以下场景（这里使用的都是系统调用函数，非Python库提供的epoll相关函数）：

- 假设pipe读取端的文件描述符rfd已经注册到epoll上
- pipe写入端向pipe中写入了2 kB数据
- 调用epoll_wait，rfd将会作为可读文件描述符返回
- pipe读取端从rfd缓冲区读入了1 kB数据
- 调用epoll_wait

如果rfd文件描述符已经注册到了带EPOLLET（edge-triggered）标志的epoll中，那么第5步中的epoll_wait(2)调用有可能阻塞，尽管此时缓冲区内可能还有可读的数据；同时，远端可能期望能根据自己发送的数据获得响应。出现这种情况的原因在于：在ET模式下，只有当被监视的fd读写状态发生改变时才会传递事件。因此在第5步中，调用者可能会一直等待数据，而此时缓冲区中却有数据。

在上述场景中，rfd上的事件发生在第2步中的写入完成（可读事件发生）以及第3步中的数据消费完毕；第4步中的读操作并没有将缓冲区的数据消费完，这就导致了第5步中epoll_wait(2)无限期阻塞的可能。

使用ET模式的应用需要使用非阻塞fd来避免读写的阻塞，使用ET模式的epoll建议使用下述处理流程：

i. 将文件描述符设为nonblocking
ii. 只有当read(2)和write(2)返回EAGAIN才开始等待事件。

# Code Example of Edge-Triggerd Mode

```py
import socket
import select

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(1)
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN | select.EPOLLET)

try:
    connections = {}
    requests = {}
    responses = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            # 在ET模式下，当某一事件发生后，被epoll_wait捕捉到
            # 当事件发生后，对数据进行处理（读/写），没有一次处理完毕时，不会再产生新的事件，
            # 此时，在后续run loop中这个fd将不会不会再有被处理的机会，其上的操作（读/写）将会一直阻塞
            #
            # 因此，监测到某一事件后，需要“完成”响应的操作（读/写）
            # “完成”有两种情况：
            #   - 一直往缓冲区写，直到缓冲区满，返回EAGAIN
            #   - 一直从缓冲区读，直到缓冲区为空，返回EAGAIN
            # 
            # 这样，后续的epoll run loop中，epoll_wait能捕获到之前返回EAGAIN而此时已经准备好了的FDs
            if fileno == serversocket.fileno():
                try:
                    while True:
                        connection, address = serversocket.accept()
                        connection.setblocking(0)
                        epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                        connections[connection.fileno()] = connection
                        requests[connection.fileno()] = b''
                        responses[connection.fileno()] = response
                except socket.error:  # EAGAIN
                    pass
            elif event & select.EPOLLIN:
                try:
                    # 一直读出，直到缓冲区为空
                    while True:
                        requests[fileno] += connections[fileno].recv(1024)
                except socket.error:
                    pass
                # 请求读入完成，修改fd事件，准备response
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
                    print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            elif event & select.EPOLLOUT:
                try:
                    # 一直写入，直到缓冲区满
                    while len(responses[fileno]) > 0:
                        byteswritten = connections[fileno].send(responses[fileno])
                        responses[fileno] = responses[fileno][byteswritten:]
                except socket.error:
                    pass
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, select.EPOLLET)
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[filenoe]
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()
```

# Performance Considerations

## Listen Backlog Queue Size

上面的例子中都有serversocket.listen()这一行，listen()函数接受一个可选的参数，这个参数就是listen backlog queue size，乘着这个机会，在此也梳理一下。

调用listen系统调用时，socket状态会变为LISTEN，此时需要为这个socket指定一个backlog。backlog通常被用来指定队列能容下的链接的个数。

在TCP建立连接的三路握手过程中，连接需要先经历SYN RECEIVED状态才能到达最终的ESTABLISHED状态，处于ESTABLISHED状态的连接才能被accept系统调用返回给应用。正因为如此，TCP/IP协议栈通常有两种实现backlog queue的策略：

1. 使用一个队列，其大小由listen系统调用的backlog参数决定。当服务器收到SYN数据包后，会发送SYN/ACK数据包给客户端并将该连接入队列；当服务器收到客户端的ACK确认数据包后，连接状态变为ESTABLISHED，该连接可以被应用程序使用。这意味着这个队列会包含SYN RECEIVED和ESTABLISHED两种状态的连接，只是只有处于ESTABLISHED状态的连接才会返回给用户程序中的accept系统调用。

2. 使用两个队列，一个SYN 队列（或者说是未完成连接队列）和一个accept 队列（或者说是连接完成队列）。处于SYN RECEIVED状态的连接会被添加到SYN队列，然后，当这一连接状态变为ESTABLISHED后，其被移至accept队列。accept系统调用只会从accept队列中消耗连接。在这种策略中，listen系统调用的backlog参数决定的是accept 队列的大小。

历史上，BSD的TCP实现使用了第一种策略。这一选择意味着当连接数到达backlog上限时，系统将不再发送SYN/ACK数据包来响应来自客户端的SYN数据包（三路握手阶段）；并且系统会丢弃SYN数据包（而不是响应RST数据包），因此客户端会重试（因为客户端没有收到ACK）。

没有太深入了解BSD的实现，按照W. Richard Stevens书中的解释，BSD实现使用了两个队列，但是实际上就像一个队列一样。队列的上限由backlog参数决定（可以不完全等于，可以乘上一个因子，比如1.5）。

Linux则不同，在linux系统调用的man page有下述解释：

> 在Linux 2.2中，TCP sockets中的backlog参数的行为发生了变化——backlog现在指定的是存放等待被accept的已完成连接socket的队列长度，而不是未完成连接请求的的数量。未完成连接队列长度大小可以用/proc/sys/net/ipv4/tcp_max_syn_backlog来设定。当syncookies开启时，没有逻辑上的最大队列长度值，这个设定会被忽略。
> 如果backlog参数比/proc/sys/net/core/somaxconn大，那么backlog会被自动调为somaxconn值；SOMAXCONN默认值为128，在Linux 2.4.25之前，这个值被hardcode在内核中。

这说明现在的Linux版本使用了两个不同的队列：一个由系统设定指定大小的SYN队列以及一个由应用程序指定大小的accept队列。

那么如果accept队列满，此时因为服务器收到了处于三路握手阶段最后的ACK数据包，需要将连接从SYN队列移至accept队列中，Linux怎么处理这种情况的呢？这用情况由net/ipv4/tcp_minisocks.c中的tcp_check_req函数处理，相关代码：

```c
child = inet_csk(sk)->icsk_af_ops->syn_recv_sock(sk, skb, req, NULL);
if (child == NULL)
    goto listen_overflow;
```

对于IPv4，第一行代码会调用net/ipv4/tcp_ipv4.c中的tcp_v4_syn_recv_sock函数，它包含以下代码：

```c
if (sk_acceptq_is_full(sk))
    goto exit_overflow;
```

可以看到，这里检查了accept queue。exit_overflow标签后面的代码会清除或更新/proc/net/netstat中的ListenOverflow和ListenDrops等统计，然后返回NULL，这回触发tcp_check_req中的listen_overflow的执行：

```c
listen_overflow:
    if (!sysctl_tcp_abort_on_overflow) {
        inet_rsk(req)->acked = 1;
        return NULL;
    }
```

这意味着，只有当`/proc/sys/net/ipv4/tcp_abort_on_overflow`设为`1`时（上面代码后面有发送RST数据包的逻辑）才有相应的处理策略。

总结起来就是，Linux的TCP实现中，当accept队列满时，服务器收到了处于三路握手阶段最后的ACK数据包后，默认会忽略这个数据包。