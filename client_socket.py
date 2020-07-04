import socket





#address = ('111.230.222.104', 8000)

def send(photo,sendFileName,address =  ('111.230.222.104', 8000)):
  print('sending {}'.format(photo))
  data = file_deal(photo)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(address)

  sock.send('{}|{}'.format(len(data), sendFileName).encode())  #默认编码 utf-8,发送文件长度和文件名
  reply = sock.recv(1024)
  if 'ok' == reply.decode():       #确认一下服务器get到文件长度和文件名数据
    go = 0
    total = len(data)
    while go < total:            #发送文件
      data_to_send = data[go:go + 1024]
      sock.send(data_to_send)
      go += len(data_to_send)
    reply = sock.recv(1024)
    if 'copy' == reply.decode():
      print('{} send successfully'.format(photo))
  sock.close()           #由于tcp是以流的形式传输数据，我们无法判断开头和结尾，简单的方法是没传送一个文件，就使用一个socket，但是这样是消耗计算机的资源，博主正在探索更好的方法，有机会交流一下


def file_deal(file_path):  #读取文件的方法
  mes = b''
  try:
    file = open(file_path,'rb')
    mes = file.read()
  except:
    print('error{}'.format(file_path))
  else:
    file.close()
    return mes



def test():
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect(address)
  while True:
      re_data = input()
      client.send(re_data.encode("utf8"))
      data = client.recv(1024)
      print(data.decode("utf8"))


