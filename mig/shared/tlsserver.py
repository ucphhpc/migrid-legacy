#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# tlsserver - Shared functions for all SSL/TLS-secured servers
# Copyright (C) 2003-2018  The MiG Project lead by Brian Vinter
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

"""Common HTTPS server functions for e.g. strict SSL/TLS setup"""

import ssl
import sys

# Mirror strong ciphers used in Apache
STRONG_CIPHERS = "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA:!DES-CBC3-SHA:!AES128-GCM-SHA256:!AES256-GCM-SHA384:!AES128-SHA256:!AES256-SHA256:!AES128-SHA:!AES256-SHA:!CAMELLIA256-SHA:!CAMELLIA128-SHA"

DEFAULT_CURVE_PRIORITY = ['prime256v1', 'secp384r1', 'secp521r1']

def hardened_ssl_context(configuration, keyfile, certfile, dhparamsfile=None,
                         ciphers=STRONG_CIPHERS,
                         curve_priority=DEFAULT_CURVE_PRIORITY):
    """Build and return a hardened native SSL context to apply to a socket"""
    _logger = configuration.logger
    _logger.info("enforcing strong SSL/TLS connections")
    _logger.debug("using SSL/TLS ciphers: %s" % ciphers)
    ssl_protocol = ssl.PROTOCOL_SSLv23
    ssl_ctx = ssl.SSLContext(ssl_protocol)
    ssl_ctx.load_cert_chain(certfile, keyfile)
    ssl_options = 0
    ssl_options |= getattr(ssl, 'OP_NO_SSLv2', 0x1000000)
    ssl_options |= getattr(ssl, 'OP_NO_SSLv3', 0x2000000)
    ssl_options |= getattr(ssl, 'OP_NO_COMPRESSION', 0x20000)
    ssl_options |= getattr(ssl, 'OP_CIPHER_SERVER_PREFERENCE', 0x400000)
    if sys.version_info[:2] >= (2, 7) and ssl_ctx:
        _logger.info("enforcing strong SSL/TLS options")
        _logger.debug("SSL/TLS options: %s" % ssl_options)
        ssl_ctx.options |= ssl_options
    else:
        _logger.info("can't enforce strong SSL/TLS options")
        _logger.warning("Upgrade to python 2.7.9+ for maximum security")

    pfs_available = False
    if dhparamsfile:
        try:
            ssl_ctx.load_dh_params(dhparamsfile)
            pfs_available = True
        except Exception, exc:
            _logger.warning("Could not load optional dhparams from %s" % \
                            dhparamsfile)
            _logger.info("""You can create a suitable dhparams file with:
openssl dhparam 2048 -out %s""" % dhparamsfile)

    # We must explicitly set curve here to actually enable ciphers
    # using them. They can provide Perfect Forward Secrecy.
    # http://stackoverflow.com/questions/32094145/python-paste-ssl-server-with-tlsv1-2-and-forward-secrecy#32101078
    # Some help for installing pyopenssl with EC support at
    # http://stackoverflow.com/questions/7340784/easy-install-pyopenssl-error/34048924#34048924
    if curve_priority:
        activated_curve = None
        for curve_name in curve_priority:
            try:
                _logger.debug("Blindly trying elliptic curve %s" % curve_name)
                ssl_ctx.set_ecdh_curve(curve_name)
                activated_curve = curve_name
                pfs_available = True
                break
            except Exception, exc:
                _logger.warning("Couldn't init elliptic curve %s: %s" % \
                                (curve_name, exc))
        if not activated_curve: 
            _logger.info("""You need a recent pyopenssl built with elliptic
curves to take advantage of this optional improved security feature""")
    
    if not pfs_available:
        _logger.warning("""No Perfect Forward Secrecy with neither 
dhparams nor elliptic curves available.""")

    ssl_ctx.set_ciphers(ciphers)
    return ssl_ctx

def hardened_openssl_context(configuration, OpenSSL, keyfile, certfile,
                             cacertfile=None, dhparamsfile=None,
                             ciphers=STRONG_CIPHERS,
                             curve_priority=DEFAULT_CURVE_PRIORITY):
    """Build and return a hardened OpenSSL context to apply to a socket"""
    _logger = configuration.logger
    SSL, crypto = OpenSSL.SSL, OpenSSL.crypto
    _logger.info("enforcing strong SSL/TLS connections")
    _logger.debug("using SSL/TLS ciphers: %s" % ciphers)
    ssl_protocol = SSL.SSLv23_METHOD
    ssl_ctx = SSL.Context(ssl_protocol)
    ssl_ctx.use_certificate_chain_file(certfile)
    ssl_ctx.use_privatekey_file(keyfile)
    if cacertfile:
        ssl_ctx.load_verify_locations(cacertfile)

    ssl_options = 0
    ssl_options |= getattr(SSL, 'OP_NO_SSLv2', 0x1000000)
    ssl_options |= getattr(SSL, 'OP_NO_SSLv3', 0x2000000)
    ssl_options |= getattr(SSL, 'OP_NO_COMPRESSION', 0x20000)
    ssl_options |= getattr(SSL, 'OP_CIPHER_SERVER_PREFERENCE', 0x400000)
    if sys.version_info[:2] >= (2, 7) and ssl_ctx:
        _logger.info("enforcing strong SSL/TLS options")
        _logger.debug("SSL/TLS options: %s" % ssl_options)
        ssl_ctx.set_options(ssl_options)
    else:
        _logger.info("can't enforce strong SSL/TLS options")
        _logger.warning("Upgrade to python 2.7.9+ for maximum security")

    pfs_available = False
    if dhparamsfile:
        try:
            ssl_ctx.load_tmp_dh(dhparamsfile)
            pfs_available = True
        except Exception, exc:
            _logger.warning("Could not load optional dhparams from %s" % \
                            dhparamsfile)
            _logger.info("""You can create a suitable dhparams file with:
openssl dhparam 2048 -out %s""" % dhparamsfile)

    # We must explicitly set curve here to actually enable ciphers
    # using them. They can provide Perfect Forward Secrecy.
    # http://stackoverflow.com/questions/32094145/python-paste-ssl-server-with-tlsv1-2-and-forward-secrecy#32101078
    # Some help for installing pyopenssl with EC support at
    # http://stackoverflow.com/questions/7340784/easy-install-pyopenssl-error/34048924#34048924
    if curve_priority:
        try:
            # Returns a python set of curves and we grab one at random
            available_curves = crypto.get_elliptic_curves()
            curve_map = dict([(i.name, i) for i in available_curves])
            for curve_name in curve_priority:
                if curve_name in curve_map.keys():
                    use_curve = curve_map[curve_name]
                    break
            _logger.debug("Found elliptic curves %s and picked %s" % \
                          (', '.join(curve_map.keys()), use_curve.name))
            ssl_ctx.set_tmp_ecdh(use_curve)
            pfs_available = True
        except Exception, exc:
            _logger.warning("Couldn't init elliptic curve ciphers: %s" % \
                            exc)
            _logger.info("""You need a recent pyopenssl built with elliptic
curves to take advantage of this optional improved security feature""")
    
    if not pfs_available:
        _logger.warning("""No Perfect Forward Secrecy with neither 
dhparams nor elliptic curves available.""")

    ssl_ctx.set_cipher_list(ciphers)
    return ssl_ctx
