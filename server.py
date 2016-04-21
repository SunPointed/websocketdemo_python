# _*_ coding:utf-8 _*_

import simplejson
import socket
import sys
import os  
import threading 
import base64  
import hashlib  
import struct
import time
import array 

HOST = 'localhost'  
PORT = 3369  

# magic is stable
MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'  

HANDSHAKE_STRING = "HTTP/1.1 101 Switching Protocols\r\n" \
                   "Upgrade:websocket\r\n" \
                   "Connection: Upgrade\r\n" \
                   "Sec-WebSocket-Accept: {1}\r\n" \
                   "WebSocket-Location: ws://{2}/chat\r\n" \
                   "WebSocket-Protocol:chat\r\n\r\n"

class Th(threading.Thread):
  def __init__(self, connection,):
    threading.Thread.__init__(self)
    self.con = connection
  def run(self):
    while True:
      try:
        # recieve
        data = self.recv_data(1024)
        length = len(data)
        if length:
          data = '回复-->' + data
          # send
          self.send_data(data)
      except:
        print('except!')
    self.con.close()

  def unpack_frame(self, num):
    data = self.con.recv(num)
    frame = {}
    byte1, byte2 = struct.unpack_from('!BB', data)
    frame['fin'] = (byte1 >> 7) & 1
    frame['opcode'] = byte1 & 0xf
    masked = (byte2 >> 7) & 1
    frame['masked'] = masked
    mask_offset = 4 if masked else 0
    payload_hint = byte2 & 0x7f
    if payload_hint < 126:
        payload_offset = 2
        payload_length = payload_hint               
    elif payload_hint == 126:
        payload_offset = 4
        payload_length = struct.unpack_from('!H',data,2)[0]
    elif payload_hint == 127:
        payload_offset = 8
        payload_length = struct.unpack_from('!Q',data,2)[0]
    frame['length'] = payload_length
    payload = array.array('B')
    payload.fromstring(data[payload_offset + mask_offset:])
    if masked:
        mask_bytes = struct.unpack_from('!BBBB',data,payload_offset)
        for i in range(len(payload)):
            payload[i] ^= mask_bytes[i % 4]
    frame['payload'] = payload.tostring()

    return frame

  def recv_data(self, num):
    frame = self.unpack_frame(num)
    return frame['payload'].decode('utf-8')

  def send_data(self, data):
    if data:
      data = str(data)
    else:
      return False
    token = b'\x81'
    data = data.encode()
    length = len(data)
    if length < 126:
      token += struct.pack('B', length)
    elif length <= 0xFFFF:
      token += struct.pack('!BH', 126, length)
    else:
      token += struct.pack('!BQ', 127, length)
    data = token + data
    self.con.send(data)
    return True

def handshake(con):
  headers = {}
  shake = con.recv(1024)
  if not len(shake):
    return False
  header, data = shake.split('\r\n\r\n'.encode(), 1)
  for line in header.split('\r\n'.encode())[1:]:
    key, val = line.split(': '.encode(), 1)
    headers[key] = val
  print(headers)
  print(headers[b'Sec-WebSocket-Key'])
  if b'Sec-WebSocket-Key' not in headers:
    print('This socket is not websocket, client close.')
    con.close()
    return False
  sec_key = headers[b'Sec-WebSocket-Key']
  res_key = base64.b64encode(hashlib.sha1((sec_key.decode("utf-8") + MAGIC_STRING).encode()).digest())
  print('res_key:',str(res_key))
  str_handshake = HANDSHAKE_STRING.replace('{1}', res_key.decode("utf-8")).replace('{2}', HOST + ':' + str(PORT))
  print('str_handshake:',str_handshake)
  con.send(str_handshake.encode())
  return True

def start_server():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    server.bind(('localhost', 3369))
    server.listen(1000)
    print('bind 3369,ready to use')
  except:
    print('Server is already running, quit')
    sys.exit()
  while True:
    connection, address = server.accept()
    print('Got connection from', address)
    if handshake(connection):
      print('handshake success')
      try:
        t = Th(connection)
        print('new thread for client...')
        t.start()
      except:
        print('start new thread error')
        connection.close()

if __name__ == '__main__':
  start_server()