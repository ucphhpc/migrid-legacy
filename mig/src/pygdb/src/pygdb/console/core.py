#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# pygdb.console.core - python gdb console core functions
# Copyright (C) 2003-2019  The MiG Project lead by Brian Vinter
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

#
# This file is a modified version of python-gdb.py from python 2.7.5:
# https://devguide.python.org/gdb/#gdb-7-and-later
#
# You can redistribute it and/or modify it under the terms of the
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2:
# https://docs.python.org/2.7/license.html
#
# From gdb 7 onwards, gdb's build can be configured --with-python, allowing gdb
# to be extended with Python code e.g. for library-specific data visualizations,
# such as for the C++ STL types.  Documentation on this API can be seen at:
# http://sourceware.org/gdb/current/onlinedocs/gdb/Python-API.html
#
#
# This python module deals with the case when the process being debugged (the
# "inferior process" in gdb parlance) is itself python, or more specifically,
# linked against libpython.  In this situation, almost every item of data is a
# (PyObject*), and having the debugger merely print their addresses is not very
# enlightening.
#
# This module embeds knowledge about the implementation details of libpython so
# that we can emit useful visualizations e.g. a string, a list, a dict, a frame
# giving file/line information and the state of local variables
#
# In particular, given a gdb.Value corresponding to a PyObject* in the inferior
# process, we can generate a "proxy value" within the gdb process.  For example,
# given a PyObject* in the inferior process that is in fact a PyListObject*
# holding three PyObject* that turn out to be PyStringObject* instances, we can
# generate a proxy value within the gdb process that is a list of strings:
#   ["foo", "bar", "baz"]

# Doing so can be expensive for complicated graphs of objects, and could take
# some time, so we also have a "write_repr" method that writes a representation
# of the data to a file-like object.  This allows us to stop the traversal by
# having the file-like object raise an exception if it gets too much data.
#
# With both "proxyval" and "write_repr" we keep track of the set of all addresses
# visited so far in the traversal, to avoid infinite recursion due to cycles in
# the graph of object references.
#
# We try to defer gdb.lookup_type() invocations for python types until as late as
# possible: for a dynamically linked python binary, when the process starts in
# the debugger, the libpython.so hasn't been dynamically loaded yet, so none of
# the type names are known to the debugger
#
# The module also extends gdb with some python-specific commands.
#

"""GDB console python core functions"""

import sys
import gdb

# Look up the gdb.Type for some standard types:
_type_char_ptr = gdb.lookup_type('char').pointer()  # char*
_type_unsigned_char_ptr = gdb.lookup_type(
    'unsigned char').pointer()  # unsigned char*
_type_void_ptr = gdb.lookup_type('void').pointer()  # void*
_type_size_t = gdb.lookup_type('size_t')

SIZEOF_VOID_P = _type_void_ptr.sizeof


Py_TPFLAGS_HEAPTYPE = (1L << 9)

Py_TPFLAGS_INT_SUBCLASS = (1L << 23)
Py_TPFLAGS_LONG_SUBCLASS = (1L << 24)
Py_TPFLAGS_LIST_SUBCLASS = (1L << 25)
Py_TPFLAGS_TUPLE_SUBCLASS = (1L << 26)
Py_TPFLAGS_STRING_SUBCLASS = (1L << 27)
Py_TPFLAGS_UNICODE_SUBCLASS = (1L << 28)
Py_TPFLAGS_DICT_SUBCLASS = (1L << 29)
Py_TPFLAGS_BASE_EXC_SUBCLASS = (1L << 30)
Py_TPFLAGS_TYPE_SUBCLASS = (1L << 31)


MAX_OUTPUT_LEN = 1024


class NullPyObjectPtr(RuntimeError):
    pass


def safety_limit(val):
    # Given a integer value from the process being debugged, limit it to some
    # safety threshold so that arbitrary breakage within said process doesn't
    # break the gdb process too much (e.g. sizes of iterations, sizes of lists)
    return min(val, 1000)


def safe_range(val):
    # As per range, but don't trust the value too much: cap it to a safety
    # threshold in case the data was corrupted
    return xrange(safety_limit(val))


class StringTruncated(RuntimeError):
    pass


class TruncatedStringIO(object):
    """Similar to cStringIO, but can truncate the output by raising a
    StringTruncated exception"""

    def __init__(self, maxlen=None):
        self._val = ''
        self.maxlen = maxlen

    def write(self, data):
        if self.maxlen:
            if len(data) + len(self._val) > self.maxlen:
                # Truncation:
                self._val += data[0:self.maxlen - len(self._val)]
                raise StringTruncated()

        self._val += data

    def getvalue(self):
        return self._val


class PyObjectPtr(object):
    """
    Class wrapping a gdb.Value that's a either a (PyObject*) within the
    inferior process, or some subclass pointer e.g. (PyStringObject*)

    There will be a subclass for every refined PyObject type that we care
    about.

    Note that at every stage the underlying pointer could be NULL, point
    to corrupt data, etc; this is the debugger, after all.
    """
    _typename = 'PyObject'

    def __init__(self, gdbval, cast_to=None):
        if cast_to:
            self._gdbval = gdbval.cast(cast_to)
        else:
            self._gdbval = gdbval

    def field(self, name):
        """
        Get the gdb.Value for the given field within the PyObject, coping with
        some python 2 versus python 3 differences.

        Various libpython types are defined using the "PyObject_HEAD" and
        "PyObject_VAR_HEAD" macros.

        In Python 2, this these are defined so that "ob_type" and (for a var
        object) "ob_size" are fields of the type in question.

        In Python 3, this is defined as an embedded PyVarObject type thus:
           PyVarObject ob_base;
        so that the "ob_size" field is located insize the "ob_base" field, and
        the "ob_type" is most easily accessed by casting back to a (PyObject*).
        """
        if self.is_null():
            raise NullPyObjectPtr(self)

        if name == 'ob_type':
            pyo_ptr = self._gdbval.cast(PyObjectPtr.get_gdb_type())
            return pyo_ptr.dereference()[name]

        if name == 'ob_size':
            try:
                # Python 2:
                return self._gdbval.dereference()[name]
            except RuntimeError:
                # Python 3:
                return self._gdbval.dereference()['ob_base'][name]

        # General case: look it up inside the object:
        return self._gdbval.dereference()[name]

    def pyop_field(self, name):
        """
        Get a PyObjectPtr for the given PyObject* field within this PyObject,
        coping with some python 2 versus python 3 differences.
        """
        return PyObjectPtr.from_pyobject_ptr(self.field(name))

    def write_field_repr(self, name, out, visited):
        """
        Extract the PyObject* field named "name", and write its representation
        to file-like object "out"
        """
        field_obj = self.pyop_field(name)
        field_obj.write_repr(out, visited)

    def get_truncated_repr(self, maxlen):
        """
        Get a repr-like string for the data, but truncate it at "maxlen" bytes
        (ending the object graph traversal as soon as you do)
        """
        out = TruncatedStringIO(maxlen)
        try:
            self.write_repr(out, set())
        except StringTruncated:
            # Truncation occurred:
            return out.getvalue() + '...(truncated)'

        # No truncation occurred:
        return out.getvalue()

    def type(self):
        return PyTypeObjectPtr(self.field('ob_type'))

    def is_null(self):
        return 0 == long(self._gdbval)

    def is_optimized_out(self):
        """
        Is the value of the underlying PyObject* visible to the debugger?

        This can vary with the precise version of the compiler used to build
        Python, and the precise version of gdb.

        See e.g. https://bugzilla.redhat.com/show_bug.cgi?id=556975 with
        PyEval_EvalFrameEx's "f"
        """
        return self._gdbval.is_optimized_out

    def safe_tp_name(self):
        try:
            return self.type().field('tp_name').string()
        except NullPyObjectPtr:
            # NULL tp_name?
            return 'unknown'
        except RuntimeError:
            # Can't even read the object at all?
            return 'unknown'

    def proxyval(self, visited):
        """
        Scrape a value from the inferior process, and try to represent it
        within the gdb process, whilst (hopefully) avoiding crashes when
        the remote data is corrupt.

        Derived classes will override this.

        For example, a PyIntObject* with ob_ival 42 in the inferior process
        should result in an int(42) in this process.

        visited: a set of all gdb.Value pyobject pointers already visited
        whilst generating this value (to guard against infinite recursion when
        visiting object graphs with loops).  Analogous to Py_ReprEnter and
        Py_ReprLeave
        """

        class FakeRepr(object):
            """
            Class representing a non-descript PyObject* value in the inferior
            process for when we don't have a custom scraper, intended to have
            a sane repr().
            """

            def __init__(self, tp_name, address):
                self.tp_name = tp_name
                self.address = address

            def __repr__(self):
                # For the NULL pointer, we have no way of knowing a type, so
                # special-case it as per
                # http://bugs.python.org/issue8032#msg100882
                if self.address == 0:
                    return '0x0'
                return '<%s at remote 0x%x>' % (self.tp_name, self.address)

        return FakeRepr(self.safe_tp_name(),
                        long(self._gdbval))

    def write_repr(self, out, visited):
        """
        Write a string representation of the value scraped from the inferior
        process to "out", a file-like object.
        """
        # Default implementation: generate a proxy value and write its repr
        # However, this could involve a lot of work for complicated objects,
        # so for derived classes we specialize this
        return out.write(repr(self.proxyval(visited)))

    @classmethod
    def subclass_from_type(cls, t):
        """
        Given a PyTypeObjectPtr instance wrapping a gdb.Value that's a
        (PyTypeObject*), determine the corresponding subclass of PyObjectPtr
        to use

        Ideally, we would look up the symbols for the global types, but that
        isn't working yet:
          (gdb) python print gdb.lookup_symbol('PyList_Type')[0].value
          Traceback (most recent call last):
            File "<string>", line 1, in <module>
          NotImplementedError: Symbol type not yet supported in Python scripts.
          Error while executing Python code.

        For now, we use tp_flags, after doing some string comparisons on the
        tp_name for some special-cases that don't seem to be visible through
        flags
        """
        try:
            tp_name = t.field('tp_name').string()
            tp_flags = int(t.field('tp_flags'))
        except RuntimeError:
            # Handle any kind of error e.g. NULL ptrs by simply using the base
            # class
            return cls

        # print 'tp_flags = 0x%08x' % tp_flags
        # print 'tp_name = %r' % tp_name

        name_map = {'bool': PyBoolObjectPtr,
                    'classobj': PyClassObjectPtr,
                    'instance': PyInstanceObjectPtr,
                    'NoneType': PyNoneStructPtr,
                    'frame': PyFrameObjectPtr,
                    'set': PySetObjectPtr,
                    'frozenset': PySetObjectPtr,
                    'builtin_function_or_method': PyCFunctionObjectPtr,
                    }
        if tp_name in name_map:
            return name_map[tp_name]

        if tp_flags & Py_TPFLAGS_HEAPTYPE:
            return HeapTypeObjectPtr

        if tp_flags & Py_TPFLAGS_INT_SUBCLASS:
            return PyIntObjectPtr
        if tp_flags & Py_TPFLAGS_LONG_SUBCLASS:
            return PyLongObjectPtr
        if tp_flags & Py_TPFLAGS_LIST_SUBCLASS:
            return PyListObjectPtr
        if tp_flags & Py_TPFLAGS_TUPLE_SUBCLASS:
            return PyTupleObjectPtr
        if tp_flags & Py_TPFLAGS_STRING_SUBCLASS:
            return PyStringObjectPtr
        if tp_flags & Py_TPFLAGS_UNICODE_SUBCLASS:
            return PyUnicodeObjectPtr
        if tp_flags & Py_TPFLAGS_DICT_SUBCLASS:
            return PyDictObjectPtr
        if tp_flags & Py_TPFLAGS_BASE_EXC_SUBCLASS:
            return PyBaseExceptionObjectPtr
        # if tp_flags & Py_TPFLAGS_TYPE_SUBCLASS:
        #    return PyTypeObjectPtr

        # Use the base class:
        return cls

    @classmethod
    def from_pyobject_ptr(cls, gdbval):
        """
        Try to locate the appropriate derived class dynamically, and cast
        the pointer accordingly.
        """
        try:
            p = PyObjectPtr(gdbval)
            cls = cls.subclass_from_type(p.type())
            return cls(gdbval, cast_to=cls.get_gdb_type())
        except RuntimeError:
            # Handle any kind of error e.g. NULL ptrs by simply using the base
            # class
            pass
        return cls(gdbval)

    @classmethod
    def get_gdb_type(cls):
        return gdb.lookup_type(cls._typename).pointer()

    def as_address(self):
        return long(self._gdbval)


class ProxyAlreadyVisited(object):
    """
    Placeholder proxy to use when protecting against infinite recursion due to
    loops in the object graph.

    Analogous to the values emitted by the users of Py_ReprEnter and Py_ReprLeave
    """

    def __init__(self, rep):
        self._rep = rep

    def __repr__(self):
        return self._rep


def _write_instance_repr(out, visited, name, pyop_attrdict, address):
    """Shared code for use by old-style and new-style classes:
    write a representation to file-like object 'out'"""
    out.write('<')
    out.write(name)

    # Write dictionary of instance attributes:
    if isinstance(pyop_attrdict, PyDictObjectPtr):
        out.write('(')
        first = True
        for pyop_arg, pyop_val in pyop_attrdict.iteritems():
            if not first:
                out.write(', ')
            first = False
            out.write(pyop_arg.proxyval(visited))
            out.write('=')
            pyop_val.write_repr(out, visited)
        out.write(')')
    out.write(' at remote 0x%x>' % address)


class InstanceProxy(object):

    def __init__(self, cl_name, attrdict, address):
        self.cl_name = cl_name
        self.attrdict = attrdict
        self.address = address

    def __repr__(self):
        if isinstance(self.attrdict, dict):
            kwargs = ', '.join(["%s=%r" % (arg, val)
                                for arg, val in self.attrdict.iteritems()])
            return '<%s(%s) at remote 0x%x>' % (self.cl_name,
                                                kwargs, self.address)
        else:
            return '<%s at remote 0x%x>' % (self.cl_name,
                                            self.address)


def _PyObject_VAR_SIZE(typeobj, nitems):
    return ((typeobj.field('tp_basicsize') +
             nitems * typeobj.field('tp_itemsize') +
             (SIZEOF_VOID_P - 1)
             ) & ~(SIZEOF_VOID_P - 1)
            ).cast(_type_size_t)


class HeapTypeObjectPtr(PyObjectPtr):
    _typename = 'PyObject'

    def get_attr_dict(self):
        """
        Get the PyDictObject ptr representing the attribute dictionary
        (or None if there's a problem)
        """
        try:
            typeobj = self.type()
            dictoffset = int_from_int(typeobj.field('tp_dictoffset'))
            if dictoffset != 0:
                if dictoffset < 0:
                    type_PyVarObject_ptr = gdb.lookup_type(
                        'PyVarObject').pointer()
                    tsize = int_from_int(self._gdbval.cast(
                        type_PyVarObject_ptr)['ob_size'])
                    if tsize < 0:
                        tsize = -tsize
                    size = _PyObject_VAR_SIZE(typeobj, tsize)
                    dictoffset += size
                    assert dictoffset > 0
                    assert dictoffset % SIZEOF_VOID_P == 0

                dictptr = self._gdbval.cast(_type_char_ptr) + dictoffset
                PyObjectPtrPtr = PyObjectPtr.get_gdb_type().pointer()
                dictptr = dictptr.cast(PyObjectPtrPtr)
                return PyObjectPtr.from_pyobject_ptr(dictptr.dereference())
        except RuntimeError:
            # Corrupt data somewhere; fail safe
            pass

        # Not found, or some kind of error:
        return None

    def proxyval(self, visited):
        """
        Support for new-style classes.

        Currently we just locate the dictionary using a transliteration to
        python of _PyObject_GetDictPtr, ignoring descriptors
        """
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('<...>')
        visited.add(self.as_address())

        pyop_attr_dict = self.get_attr_dict()
        if pyop_attr_dict:
            attr_dict = pyop_attr_dict.proxyval(visited)
        else:
            attr_dict = {}
        tp_name = self.safe_tp_name()

        # New-style class:
        return InstanceProxy(tp_name, attr_dict, long(self._gdbval))

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('<...>')
            return
        visited.add(self.as_address())

        pyop_attrdict = self.get_attr_dict()
        _write_instance_repr(out, visited,
                             self.safe_tp_name(),
                             pyop_attrdict,
                             self.as_address())


class ProxyException(Exception):
    def __init__(self, tp_name, args):
        self.tp_name = tp_name
        self.args = args

    def __repr__(self):
        return '%s%r' % (self.tp_name, self.args)


class PyBaseExceptionObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyBaseExceptionObject* i.e. an exception
    within the process being debugged.
    """
    _typename = 'PyBaseExceptionObject'

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('(...)')
        visited.add(self.as_address())
        arg_proxy = self.pyop_field('args').proxyval(visited)
        return ProxyException(self.safe_tp_name(),
                              arg_proxy)

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('(...)')
            return
        visited.add(self.as_address())

        out.write(self.safe_tp_name())
        self.write_field_repr('args', out, visited)


class PyBoolObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyBoolObject* i.e. one of the two
    <bool> instances (Py_True/Py_False) within the process being debugged.
    """
    _typename = 'PyBoolObject'

    def proxyval(self, visited):
        if int_from_int(self.field('ob_ival')):
            return True
        else:
            return False


class PyClassObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyClassObject* i.e. a <classobj>
    instance within the process being debugged.
    """
    _typename = 'PyClassObject'


class BuiltInFunctionProxy(object):
    def __init__(self, ml_name):
        self.ml_name = ml_name

    def __repr__(self):
        return "<built-in function %s>" % self.ml_name


class BuiltInMethodProxy(object):
    def __init__(self, ml_name, pyop_m_self):
        self.ml_name = ml_name
        self.pyop_m_self = pyop_m_self

    def __repr__(self):
        return ('<built-in method %s of %s object at remote 0x%x>'
                % (self.ml_name,
                   self.pyop_m_self.safe_tp_name(),
                   self.pyop_m_self.as_address())
                )


class PyCFunctionObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyCFunctionObject*
    (see Include/methodobject.h and Objects/methodobject.c)
    """
    _typename = 'PyCFunctionObject'

    def proxyval(self, visited):
        m_ml = self.field('m_ml')  # m_ml is a (PyMethodDef*)
        ml_name = m_ml['ml_name'].string()

        pyop_m_self = self.pyop_field('m_self')
        if pyop_m_self.is_null():
            return BuiltInFunctionProxy(ml_name)
        else:
            return BuiltInMethodProxy(ml_name, pyop_m_self)


class PyCodeObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyCodeObject* i.e. a <code> instance
    within the process being debugged.
    """
    _typename = 'PyCodeObject'

    def addr2line(self, addrq):
        """
        Get the line number for a given bytecode offset

        Analogous to PyCode_Addr2Line; translated from pseudocode in
        Objects/lnotab_notes.txt
        """
        co_lnotab = self.pyop_field('co_lnotab').proxyval(set())

        # Initialize lineno to co_firstlineno as per PyCode_Addr2Line
        # not 0, as lnotab_notes.txt has it:
        lineno = int_from_int(self.field('co_firstlineno'))

        addr = 0
        for addr_incr, line_incr in zip(co_lnotab[::2], co_lnotab[1::2]):
            addr += ord(addr_incr)
            if addr > addrq:
                return lineno
            lineno += ord(line_incr)
        return lineno


class PyDictObjectPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyDictObject* i.e. a dict instance
    within the process being debugged.
    """
    _typename = 'PyDictObject'

    def iteritems(self):
        """
        Yields a sequence of (PyObjectPtr key, PyObjectPtr value) pairs,
        analagous to dict.iteritems()
        """
        for i in safe_range(self.field('ma_mask') + 1):
            ep = self.field('ma_table') + i
            pyop_value = PyObjectPtr.from_pyobject_ptr(ep['me_value'])
            if not pyop_value.is_null():
                pyop_key = PyObjectPtr.from_pyobject_ptr(ep['me_key'])
                yield (pyop_key, pyop_value)

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('{...}')
        visited.add(self.as_address())

        result = {}
        for pyop_key, pyop_value in self.iteritems():
            proxy_key = pyop_key.proxyval(visited)
            proxy_value = pyop_value.proxyval(visited)
            result[proxy_key] = proxy_value
        return result

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('{...}')
            return
        visited.add(self.as_address())

        out.write('{')
        first = True
        for pyop_key, pyop_value in self.iteritems():
            if not first:
                out.write(', ')
            first = False
            pyop_key.write_repr(out, visited)
            out.write(': ')
            pyop_value.write_repr(out, visited)
        out.write('}')


class PyInstanceObjectPtr(PyObjectPtr):
    _typename = 'PyInstanceObject'

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('<...>')
        visited.add(self.as_address())

        # Get name of class:
        in_class = self.pyop_field('in_class')
        cl_name = in_class.pyop_field('cl_name').proxyval(visited)

        # Get dictionary of instance attributes:
        in_dict = self.pyop_field('in_dict').proxyval(visited)

        # Old-style class:
        return InstanceProxy(cl_name, in_dict, long(self._gdbval))

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('<...>')
            return
        visited.add(self.as_address())

        # Old-style class:

        # Get name of class:
        in_class = self.pyop_field('in_class')
        cl_name = in_class.pyop_field('cl_name').proxyval(visited)

        # Get dictionary of instance attributes:
        pyop_in_dict = self.pyop_field('in_dict')

        _write_instance_repr(out, visited,
                             cl_name, pyop_in_dict, self.as_address())


class PyIntObjectPtr(PyObjectPtr):
    _typename = 'PyIntObject'

    def proxyval(self, visited):
        result = int_from_int(self.field('ob_ival'))
        return result


class PyListObjectPtr(PyObjectPtr):
    _typename = 'PyListObject'

    def __getitem__(self, i):
        # Get the gdb.Value for the (PyObject*) with the given index:
        field_ob_item = self.field('ob_item')
        return field_ob_item[i]

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('[...]')
        visited.add(self.as_address())

        result = [PyObjectPtr.from_pyobject_ptr(self[i]).proxyval(visited)
                  for i in safe_range(int_from_int(self.field('ob_size')))]
        return result

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('[...]')
            return
        visited.add(self.as_address())

        out.write('[')
        for i in safe_range(int_from_int(self.field('ob_size'))):
            if i > 0:
                out.write(', ')
            element = PyObjectPtr.from_pyobject_ptr(self[i])
            element.write_repr(out, visited)
        out.write(']')


class PyLongObjectPtr(PyObjectPtr):
    _typename = 'PyLongObject'

    def proxyval(self, visited):
        """
        Python's Include/longobjrep.h has this declaration:
           struct _longobject {
               PyObject_VAR_HEAD
               digit ob_digit[1];
           };

        with this description:
            The absolute value of a number is equal to
                 SUM(for i=0 through abs(ob_size)-1) ob_digit[i] * 2**(SHIFT*i)
            Negative numbers are represented with ob_size < 0;
            zero is represented by ob_size == 0.

        where SHIFT can be either:
            #define PyLong_SHIFT        30
            #define PyLong_SHIFT        15
        """
        ob_size = long(self.field('ob_size'))
        if ob_size == 0:
            return 0L

        ob_digit = self.field('ob_digit')

        if gdb.lookup_type('digit').sizeof == 2:
            SHIFT = 15L
        else:
            SHIFT = 30L

        digits = [long(ob_digit[i]) * 2**(SHIFT*i)
                  for i in safe_range(abs(ob_size))]
        result = sum(digits)
        if ob_size < 0:
            result = -result
        return result


class PyNoneStructPtr(PyObjectPtr):
    """
    Class wrapping a gdb.Value that's a PyObject* pointing to the
    singleton (we hope) _Py_NoneStruct with ob_type PyNone_Type
    """
    _typename = 'PyObject'

    def proxyval(self, visited):
        return None


class PyFrameObjectPtr(PyObjectPtr):
    _typename = 'PyFrameObject'

    def __init__(self, gdbval, cast_to):
        PyObjectPtr.__init__(self, gdbval, cast_to)

        if not self.is_optimized_out():
            self.co = PyCodeObjectPtr.from_pyobject_ptr(self.field('f_code'))
            self.co_name = self.co.pyop_field('co_name')
            self.co_filename = self.co.pyop_field('co_filename')
            self.f_lineno = int_from_int(self.field('f_lineno'))
            self.f_lasti = int_from_int(self.field('f_lasti'))
            self.co_nlocals = int_from_int(self.co.field('co_nlocals'))
            self.co_varnames = PyTupleObjectPtr.from_pyobject_ptr(
                self.co.field('co_varnames'))
            self.f_back = self.field('f_back')

    def iter_locals(self):
        """
        Yield a sequence of (name,value) pairs of PyObjectPtr instances, for
        the local variables of this frame
        """
        if self.is_optimized_out():
            return

        f_localsplus = self.field('f_localsplus')
        for i in safe_range(self.co_nlocals):
            pyop_value = PyObjectPtr.from_pyobject_ptr(f_localsplus[i])
            if not pyop_value.is_null():
                pyop_name = PyObjectPtr.from_pyobject_ptr(self.co_varnames[i])
                yield (pyop_name, pyop_value)

    def iter_globals(self):
        """
        Yield a sequence of (name,value) pairs of PyObjectPtr instances, for
        the global variables of this frame
        """
        if self.is_optimized_out():
            return

        pyop_globals = self.pyop_field('f_globals')
        return pyop_globals.iteritems()

    def iter_builtins(self):
        """
        Yield a sequence of (name,value) pairs of PyObjectPtr instances, for
        the builtin variables
        """
        if self.is_optimized_out():
            return

        pyop_builtins = self.pyop_field('f_builtins')
        return pyop_builtins.iteritems()

    def get_var_by_name(self, name):
        """
        Look for the named local variable, returning a (PyObjectPtr, scope) pair
        where scope is a string 'local', 'global', 'builtin'

        If not found, return (None, None)
        """
        for pyop_name, pyop_value in self.iter_locals():
            if name == pyop_name.proxyval(set()):
                return pyop_value, 'local'
        for pyop_name, pyop_value in self.iter_globals():
            if name == pyop_name.proxyval(set()):
                return pyop_value, 'global'
        for pyop_name, pyop_value in self.iter_builtins():
            if name == pyop_name.proxyval(set()):
                return pyop_value, 'builtin'
        return None, None

    def filename(self):
        """Get the path of the current Python source file, as a string"""
        if self.is_optimized_out():
            return '(frame information optimized out)'
        return self.co_filename.proxyval(set())

    def current_line_num(self):
        """Get current line number as an integer (1-based)

        Translated from PyFrame_GetLineNumber and PyCode_Addr2Line

        See Objects/lnotab_notes.txt
        """
        if self.is_optimized_out():
            return None
        f_trace = self.field('f_trace')
        if long(f_trace) != 0:
            # we have a non-NULL f_trace:
            return self.f_lineno
        else:
            # try:
            return self.co.addr2line(self.f_lasti)
            # except ValueError:
            #    return self.f_lineno

    def current_line(self):
        """Get the text of the current source line as a string, with a trailing
        newline character"""
        if self.is_optimized_out():
            return '(frame information optimized out)'
        with open(self.filename(), 'r') as f:
            all_lines = f.readlines()
            # Convert from 1-based current_line_num to 0-based list offset:
            return all_lines[self.current_line_num()-1]

    def write_repr(self, out, visited):
        if self.is_optimized_out():
            out.write('(frame information optimized out)')
            return
        out.write('Frame 0x%x, for file %s, line %i, in %s ('
                  % (self.as_address(),
                     self.co_filename,
                     self.current_line_num(),
                     self.co_name))
        first = True
        for pyop_name, pyop_value in self.iter_locals():
            if not first:
                out.write(', ')
            first = False

            out.write(pyop_name.proxyval(visited))
            out.write('=')
            pyop_value.write_repr(out, visited)

        out.write(')')


class PySetObjectPtr(PyObjectPtr):
    _typename = 'PySetObject'

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('%s(...)' % self.safe_tp_name())
        visited.add(self.as_address())

        members = []
        table = self.field('table')
        for i in safe_range(self.field('mask')+1):
            setentry = table[i]
            key = setentry['key']
            if key != 0:
                key_proxy = PyObjectPtr.from_pyobject_ptr(
                    key).proxyval(visited)
                if key_proxy != '<dummy key>':
                    members.append(key_proxy)
        if self.safe_tp_name() == 'frozenset':
            return frozenset(members)
        else:
            return set(members)

    def write_repr(self, out, visited):
        out.write(self.safe_tp_name())

        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('(...)')
            return
        visited.add(self.as_address())

        out.write('([')
        first = True
        table = self.field('table')
        for i in safe_range(self.field('mask')+1):
            setentry = table[i]
            key = setentry['key']
            if key != 0:
                pyop_key = PyObjectPtr.from_pyobject_ptr(key)
                key_proxy = pyop_key.proxyval(visited)  # FIXME!
                if key_proxy != '<dummy key>':
                    if not first:
                        out.write(', ')
                    first = False
                    pyop_key.write_repr(out, visited)
        out.write('])')


class PyStringObjectPtr(PyObjectPtr):
    _typename = 'PyStringObject'

    def __str__(self):
        field_ob_size = self.field('ob_size')
        field_ob_sval = self.field('ob_sval')
        char_ptr = field_ob_sval.address.cast(_type_unsigned_char_ptr)
        return ''.join([chr(char_ptr[i]) for i in safe_range(field_ob_size)])

    def proxyval(self, visited):
        return str(self)


class PyTupleObjectPtr(PyObjectPtr):
    _typename = 'PyTupleObject'

    def __getitem__(self, i):
        # Get the gdb.Value for the (PyObject*) with the given index:
        field_ob_item = self.field('ob_item')
        return field_ob_item[i]

    def proxyval(self, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            return ProxyAlreadyVisited('(...)')
        visited.add(self.as_address())

        result = tuple([PyObjectPtr.from_pyobject_ptr(
            self[i]).proxyval(visited)
            for i in safe_range(int_from_int(self.field('ob_size')))])
        return result

    def write_repr(self, out, visited):
        # Guard against infinite loops:
        if self.as_address() in visited:
            out.write('(...)')
            return
        visited.add(self.as_address())

        out.write('(')
        for i in safe_range(int_from_int(self.field('ob_size'))):
            if i > 0:
                out.write(', ')
            element = PyObjectPtr.from_pyobject_ptr(self[i])
            element.write_repr(out, visited)
        if self.field('ob_size') == 1:
            out.write(',)')
        else:
            out.write(')')


class PyTypeObjectPtr(PyObjectPtr):
    _typename = 'PyTypeObject'


class PyUnicodeObjectPtr(PyObjectPtr):
    _typename = 'PyUnicodeObject'

    def proxyval(self, visited):
        # From unicodeobject.h:
        #     Py_ssize_t length;  /* Length of raw Unicode data in buffer */
        #     Py_UNICODE *str;    /* Raw Unicode buffer */
        field_length = long(self.field('length'))
        field_str = self.field('str')

        # Gather a list of ints from the Py_UNICODE array; these are either
        # UCS-2 or UCS-4 code points:
        Py_UNICODEs = [int(field_str[i]) for i in safe_range(field_length)]

        # Convert the int code points to unicode characters, and generate a
        # local unicode instance:
        result = u''.join([unichr(ucs) for ucs in Py_UNICODEs])
        return result


def int_from_int(gdbval):
    return int(str(gdbval))


class Frame(object):
    """
    Wrapper for gdb.Frame, adding various methods
    """

    def __init__(self, gdbframe):
        self._gdbframe = gdbframe

    def older(self):
        older = self._gdbframe.older()
        if older:
            return Frame(older)
        else:
            return None

    def newer(self):
        newer = self._gdbframe.newer()
        if newer:
            return Frame(newer)
        else:
            return None

    def select(self):
        self._gdbframe.select()

    def get_index(self):
        """Calculate index of frame, starting at 0 for the newest frame within
        this thread"""
        index = 0
        # Go down until you reach the newest frame:
        iter_frame = self
        while iter_frame.newer():
            index += 1
            iter_frame = iter_frame.newer()
        return index

    def is_evalframeex(self):
        if self._gdbframe.function():
            if self._gdbframe.function().name == 'PyEval_EvalFrameEx':
                """
                I believe we also need to filter on the inline
                struct frame_id.inline_depth, only regarding frames with
                an inline depth of 0 as actually being this function

                So we reject those with type gdb.INLINE_FRAME
                """
                if self._gdbframe.type() == gdb.NORMAL_FRAME:
                    # We have a PyEval_EvalFrameEx frame:
                    return True

        return False

    def get_pyop(self):
        try:
            f = self._gdbframe.read_var('f')
            return PyFrameObjectPtr.from_pyobject_ptr(f)
        except ValueError:
            return None

    @classmethod
    def get_selected_frame(cls):
        _gdbframe = gdb.selected_frame()
        if _gdbframe:
            return Frame(_gdbframe)
        return None

    @classmethod
    def get_selected_python_frame(cls):
        """Try to obtain the Frame for the python code in the selected frame,
        or None"""
        frame = cls.get_selected_frame()

        while frame:
            if frame.is_evalframeex():
                return frame
            frame = frame.older()

        # Not found:
        return None

    def print_summary(self):
        if self.is_evalframeex():
            pyop = self.get_pyop()
            if pyop:
                sys.stdout.write('#%i %s\n' % (
                    self.get_index(), pyop.get_truncated_repr(MAX_OUTPUT_LEN)))
                sys.stdout.write(pyop.current_line())
            else:
                sys.stdout.write(
                    '#%i (unable to read python frame information)\n'
                    % self.get_index())
        else:
            sys.stdout.write('#%i\n' % self.get_index())


def move_in_stack(move_up, silently=False):
    """Move up or down the stack (for the py-up/py-down command)"""
    frame = Frame.get_selected_python_frame()
    while frame:
        if move_up:
            iter_frame = frame.older()
        else:
            iter_frame = frame.newer()

        if not iter_frame:
            break

        if iter_frame.is_evalframeex():
            # Result:
            iter_frame.select()
            if not silently:
                iter_frame.print_summary()
            return True

        frame = iter_frame

    if not silently:
        if move_up:
            print 'Unable to find an older python frame'
        else:
            print 'Unable to find a newer python frame'

    return False
