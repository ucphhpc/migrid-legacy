#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# Proxy Agent - Agent enabling secured ingoing traffic via a MiG proxy
#               without opening services to anything other than localhost.
#
# Can be used as either a library or a command-line client.
#
# @author Simon Andreas Frimann Lund
#
# Copyright (C) 2003-2009  The MiG Project lead by Brian Vinter
#
# This file is part of MiG.
#
# MiG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MiG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#
import time, socket, sys, os, logging
from struct import unpack, pack
from threading import Thread
from OpenSSL import SSL

from proxy.plumber import *
from proxy import mip

logging.basicConfig(filename='proxyagent.log',level=logging.DEBUG)

# Proxy agent
def verify_cb(conn, cert, errnum, depth, ok):
  logging.debug('Proxy certificate: %s %s' % (cert.get_subject(), ok))
  return ok

control_socket = None # Life-line to the proxy
connections = []      # List of connections to close and cleanup gracefully
buffer_size = 4096    # Must be mod 2, 4096 might be too big for some...
                      # but it is much faster if it's supported

def connect(host, port, identity, tls=True):
    
  # Connect to proxy and identify
  handshake(host, port, identity)
  
  # Handle Setup request forever
  while 1:
    
    try:
      
      data = control_socket.recv(1) # Get the message type
      
      if (data == mip.messages['SETUP_REQUEST']):
        
        (ticket,) = unpack('!I', control_socket.recv(4))        
        (proxy_host_length,) = unpack('!I', control_socket.recv(4))
        proxy_host = control_socket.recv(proxy_host_length)      
        (proxy_port,) = unpack('!I', control_socket.recv(4))
        
        (machine_host_length,) = unpack('!I', control_socket.recv(4))
        machine_host = control_socket.recv(machine_host_length)
        (machine_port,) = unpack('!I', control_socket.recv(4))
        
        handle_setup_request(ticket, proxy_host, proxy_port, machine_host, machine_port, tls)
      else:
        logging.debug('CLIENT: Broken data! %s' % repr(data))
      
    except:
      logging.debug('CLIENT: Unexpected error, shutting down control connection.')
      control_socket.close()
      break

"""
  handshake,
 
  Identify proxy agent to proxy server
  TODO: catch those exceptions and add return error code...
"""
def handshake(host, port, identity, tls=True):
  
  global control_socket
  handshakeMessage = mip.handshake(1, identity)
  
  dir = os.path.dirname(sys.argv[0])
  if dir == '':
      dir = os.curdir
  
  if tls:
    # Initialize context
    ctx = SSL.Context(SSL.TLSv1_METHOD)
    ctx.set_verify(SSL.VERIFY_NONE, verify_cb)
    ctx.use_privatekey_file (os.path.join(dir, 'certs/client.pkey'))
    ctx.use_certificate_file(os.path.join(dir, 'certs/client.cert'))
    ctx.load_verify_locations(os.path.join(dir, 'certs/CA.cert'))
    
    # Set up client
    control_socket = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
  else:

    control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  control_socket.connect((host, port))
  control_socket.send(handshakeMessage)      

"""
 handle_setup_request,
 
 Set's up a new tunnel between local endpoint and proxy server
"""
def handle_setup_request(ticket, proxy_host, proxy_port, machine_host, machine_port, tls=True):
  
  global control_socket
  
  logging.debug('CLIENT: Performing setup %s (phost:%s,pport:%s,mhost:%s,mport:%s)' % (ticket, proxy_host, proxy_port, machine_host, machine_port))
  
  # Connect to proxy
  dir = os.path.dirname(sys.argv[0])
  if dir == '':
      dir = os.curdir
  
  proxyConnected    = False
  endPointConnected = False

  # Connect to endpoint  
  try:
    endpoint = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endpoint.connect((machine_host, machine_port))
  
    endPointConnected = True
  except:
    logging.debug('CLIENT: Socket error when contacting endpoint.')
  
  # Connect to proxy and prepend setup response
  if endPointConnected:
    try:
      
      if tls:
        # Initialize context
        ctx = SSL.Context(SSL.TLSv1_METHOD)
        ctx.set_verify(SSL.VERIFY_NONE, verify_cb) # Demand a certificate
        ctx.use_privatekey_file (os.path.join(dir, 'certs/client.pkey'))
        ctx.use_certificate_file(os.path.join(dir, 'certs/client.cert'))
        ctx.load_verify_locations(os.path.join(dir, 'certs/CA.cert'))
                
        proxy_socket = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      else:
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
      proxy_socket.connect((proxy_host, proxy_port))
                    
      proxyConnected = True
    except:
      logging.debug('CLIENT: Socket error when contacting proxy.')
  
  # Send status to the connection handler in proxy
  if proxyConnected:
    proxy_socket.sendall(mip.setup_response(ticket, int(endPointConnected and proxyConnected)))
  
  # Send status back over control line to proxy  
  control_socket.sendall(mip.setup_response(ticket,int(endPointConnected and proxyConnected)))  
  
  # Setup tunnel between proxy and endpoint  
  if proxyConnected and endPointConnected:
    
    # Add connections to list so they can be shut down gracefully
    connections.append(endpoint)
    connections.append(proxy_socket)
    mario = PlumberTS(endpoint, proxy_socket, 4096, True)
    #mario = Plumber(endpoint, ss, 1024, True)
    logging.debug('CLIENT: Setup done!')
    
  else:
    logging.debug('CLIENT: Setup Failure!')
  
  return proxyConnected and endPointConnected

if __name__ == '__main__':
  
  if len(sys.argv) < 5:
    print 'Usage: python[2] mipclient.py HOST PORT IDENTIFIER SSL'
    sys.exit(1)

  # TODO: - Sanitize commandline arguments
  #       - Provide cert files as commandline arguments
  try:
    connect(sys.argv[1], int(sys.argv[2]), sys.argv[3], (sys.argv[4] == 'SSL'))
  except KeyboardInterrupt:

    logging.debug('CLIENT: User interrupted, shutting down connections.')
    for conn in connections:
      logging.debug('%s ' % conn)
      conn.close()
    logging.debug('CLIENT: Shut down control connection.')
    control_socket.close()
    logging.debug('CLIENT: Control connection is down.')
    exit(0)
  
else:
  pass