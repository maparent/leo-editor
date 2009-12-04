#@+leo-ver=4-thin
#@+node:ekr.20091204131831.6103:@thin ../external/path.py
#@@language python
#@@tabwidth -4

#@<< docstring >>
#@+node:ekr.20091204132801.6169:<< docstring >>
""" path.py - An object representing a path to a file or directory.

Example:

from path import path
d = path('/home/guido/bin')
for f in d.files('*.py'):
    f.chmod(0755)

This module requires Python 2.2 or later.


URL:     http://www.jorendorff.com/articles/python/path
Author:  Jason Orendorff <jason@jorendorff.com> (and others - see the url!)
Date:    7 Mar 2004
"""
#@-node:ekr.20091204132801.6169:<< docstring >>
#@nl
#@<< todo >>
#@+node:ekr.20091204132801.6170:<< todo >>
#@+at
# TODO
# - Bug in write_text().  It doesn't support Universal newline mode.
# - Better error message in listdir() when self isn't a
#   directory. (On Windows, the error message really sucks.)
# - Make sure everything has a good docstring.
# - Add methods for regex find and replace.
# - guess_content_type() method?
# - Perhaps support arguments to touch().
# - Could add split() and join() methods that generate warnings.
# - Note:  __add__() technically has a bug, I think, where
#   it doesn't play nice with other types that implement
# __radd__().  Test this.
#@-at
#@-node:ekr.20091204132801.6170:<< todo >>
#@nl
#@<< imports >>
#@+node:ekr.20091204132801.6171:<< imports >>
from __future__ import generators

import sys, os, fnmatch, glob, shutil, codecs

isPython3 = sys.version_info >= (3,0,0)

__version__ = '2.0.4'
__all__ = ['path']
#@-node:ekr.20091204132801.6171:<< imports >>
#@nl
#@<< defines >>
#@+node:ekr.20091204132801.2686:<< defines >>
# Pre-2.3 support.  Are unicode filenames supported?

if isPython3:
    _base = str
else:
    _base = unicode
    # Pre-2.3 workaround for basestring.
    try:
        basestring
    except NameError:
        basestring = (str, unicode)

# _base = str
# try:
    # if os.path.supports_unicode_filenames:
        # _base = unicode
# except AttributeError:
    # pass

# Universal newline support
_textmode = 'r'
if not isPython3:
    if hasattr(file, 'newlines'):
        _textmode = 'U'
#@-node:ekr.20091204132801.2686:<< defines >>
#@nl

#@+others
#@+node:ekr.20091204132801.2687:class path
class path(_base):
    """ Represents a filesystem path.

    For documentation on individual methods, consult their
    counterparts in os.path.
    """

    #@    @+others
    #@+node:ekr.20091204132801.6173:Special methods
    def __repr__(self):
        return 'path(%s)' % _base.__repr__(self)

    # Adding a path and a string yields a path.
    def __add__(self, more):
        return path(_base(self) + more)

    def __radd__(self, other):
        return path(other + _base(self))

    # The / operator joins paths.
    def __div__(self, rel):
        """ fp.__div__(rel) == fp / rel == fp.joinpath(rel)

        Join two path components, adding a separator character if
        needed.
        """
        return path(os.path.join(self, rel))

    # Make the / operator work even when true division is enabled.
    __truediv__ = __div__
    #@-node:ekr.20091204132801.6173:Special methods
    #@+node:ekr.20091204132801.2692:getcwd
    def getcwd():
        """ Return the current working directory as a path object. """
        return path(os.getcwd())

    getcwd = staticmethod(getcwd)
    #@-node:ekr.20091204132801.2692:getcwd
    #@+node:ekr.20091204132801.6174:path strings...
    #@+node:ekr.20091204132801.2693:abspath

    # --- Operations on path strings.

    def abspath(self):       return path(os.path.abspath(self))
    #@-node:ekr.20091204132801.2693:abspath
    #@+node:ekr.20091204132801.2694:normcase
    def normcase(self):
        return path(os.path.normcase(self))
    #@-node:ekr.20091204132801.2694:normcase
    #@+node:ekr.20091204132801.2695:normpath
    def normpath(self):
        return path(os.path.normpath(self))
    #@-node:ekr.20091204132801.2695:normpath
    #@+node:ekr.20091204132801.2696:realpath
    def realpath(self):
        return path(os.path.realpath(self))
    #@-node:ekr.20091204132801.2696:realpath
    #@+node:ekr.20091204132801.2697:expanduser
    def expanduser(self):
        return path(os.path.expanduser(self))
    #@-node:ekr.20091204132801.2697:expanduser
    #@+node:ekr.20091204132801.2698:expandvars
    def expandvars(self):
        return path(os.path.expandvars(self))
    #@-node:ekr.20091204132801.2698:expandvars
    #@+node:ekr.20091204132801.2699:dirname
    def dirname(self):
        return path(os.path.dirname(self))
    #@-node:ekr.20091204132801.2699:dirname
    #@+node:ekr.20091204132801.2700:expand
    basename = os.path.basename

    def expand(self):
        """ Clean up a filename by calling expandvars(),
        expanduser(), and normpath() on it.

        This is commonly everything needed to clean up a filename
        read from a configuration file, for example.
        """
        return self.expandvars().expanduser().normpath()
    #@-node:ekr.20091204132801.2700:expand
    #@+node:ekr.20091204132801.2701:_get_namebase
    def _get_namebase(self):

        base, ext = os.path.splitext(self.name)
        return base

    #@-node:ekr.20091204132801.2701:_get_namebase
    #@+node:ekr.20091204132801.2702:_get_ext
    def _get_ext(self):
        f, ext = os.path.splitext(_base(self))
        return ext

    #@-node:ekr.20091204132801.2702:_get_ext
    #@+node:ekr.20091204132801.2703:_get_drive
    def _get_drive(self):
        drive, r = os.path.splitdrive(self)
        return path(drive)
    #@-node:ekr.20091204132801.2703:_get_drive
    #@+node:ekr.20091204132801.2704:splitpath
    parent = property(
        dirname, None, None,
        """ This path's parent directory, as a new path object.

        For example, path('/usr/local/lib/libpython.so').parent == path('/usr/local/lib')
        """)

    name = property(
        basename, None, None,
        """ The name of this file or directory without the full path.

        For example, path('/usr/local/lib/libpython.so').name == 'libpython.so'
        """)

    namebase = property(
        _get_namebase, None, None,
        """ The same as path.name, but with one file extension stripped off.

        For example, path('/home/guido/python.tar.gz').name     == 'python.tar.gz',
        but          path('/home/guido/python.tar.gz').namebase == 'python.tar'
        """)

    ext = property(
        _get_ext, None, None,
        """ The file extension, for example '.py'. """)

    drive = property(
        _get_drive, None, None,
        """ The drive specifier, for example 'C:'.
        This is always empty on systems that don't use drive specifiers.
        """)

    def splitpath(self):
        """ p.splitpath() -> Return (p.parent, p.name). """
        parent, child = os.path.split(self)
        return path(parent), child

    #@-node:ekr.20091204132801.2704:splitpath
    #@+node:ekr.20091204132801.2705:splitdrive
    def splitdrive(self):
        """ p.splitdrive() -> Return (p.drive, <the rest of p>).

        Split the drive specifier from this path.  If there is
        no drive specifier, p.drive is empty, so the return value
        is simply (path(''), p).  This is always the case on Unix.
        """
        drive, rel = os.path.splitdrive(self)
        return path(drive), rel

    #@-node:ekr.20091204132801.2705:splitdrive
    #@+node:ekr.20091204132801.2706:splitext
    def splitext(self):
        """ p.splitext() -> Return (p.stripext(), p.ext).

        Split the filename extension from this path and return
        the two parts.  Either part may be empty.

        The extension is everything from '.' to the end of the
        last path segment.  This has the property that if
        (a, b) == p.splitext(), then a + b == p.
        """
        filename, ext = os.path.splitext(self)
        return path(filename), ext

    #@-node:ekr.20091204132801.2706:splitext
    #@+node:ekr.20091204132801.2707:stripext
    def stripext(self):
        """ p.stripext() -> Remove one file extension from the path.

        For example, path('/home/guido/python.tar.gz').stripext()
        returns path('/home/guido/python.tar').
        """
        return self.splitext()[0]

    #@-node:ekr.20091204132801.2707:stripext
    #@+node:ekr.20091204132801.2708:splitunc
    if hasattr(os.path, 'splitunc'):
        def splitunc(self):
            unc, rest = os.path.splitunc(self)
            return path(unc), rest

        def _get_uncshare(self):
            unc, r = os.path.splitunc(self)
            return path(unc)

        uncshare = property(
            _get_uncshare, None, None,
            """ The UNC mount point for this path.
            This is empty for paths on local drives. """)

    #@-node:ekr.20091204132801.2708:splitunc
    #@+node:ekr.20091204132801.2709:joinpath
    def joinpath(self, *args):
        """ Join two or more path components, adding a separator
        character (os.sep) if needed.  Returns a new path
        object.
        """
        return path(os.path.join(self, *args))

    #@-node:ekr.20091204132801.2709:joinpath
    #@+node:ekr.20091204132801.2710:splitall
    def splitall(self):
        """ Return a list of the path components in this path.

        The first item in the list will be a path.  Its value will be
        either os.curdir, os.pardir, empty, or the root directory of
        this path (for example, '/' or 'C:\\').  The other items in
        the list will be strings.

        path.path.joinpath(*result) will yield the original path.
        """
        parts = []
        loc = self
        while loc != os.curdir and loc != os.pardir:
            prev = loc
            loc, child = prev.splitpath()
            if loc == prev:
                break
            parts.append(child)
        parts.append(loc)
        parts.reverse()
        return parts

    #@-node:ekr.20091204132801.2710:splitall
    #@+node:ekr.20091204132801.2711:relpath
    def relpath(self):
        """ Return this path as a relative path,
        based from the current working directory.
        """
        cwd = path(os.getcwd())
        return cwd.relpathto(self)

    #@-node:ekr.20091204132801.2711:relpath
    #@+node:ekr.20091204132801.2712:relpathto
    def relpathto(self, dest):
        """ Return a relative path from self to dest.

        If there is no relative path from self to dest, for example if
        they reside on different drives in Windows, then this returns
        dest.abspath().
        """
        origin = self.abspath()
        dest = path(dest).abspath()

        orig_list = origin.normcase().splitall()
        # Don't normcase dest!  We want to preserve the case.
        dest_list = dest.splitall()

        if orig_list[0] != os.path.normcase(dest_list[0]):
            # Can't get here from there.
            return dest

        # Find the location where the two paths start to differ.
        i = 0
        for start_seg, dest_seg in zip(orig_list, dest_list):
            if start_seg != os.path.normcase(dest_seg):
                break
            i += 1

        # Now i is the point where the two paths diverge.
        # Need a certain number of "os.pardir"s to work up
        # from the origin to the point of divergence.
        segments = [os.pardir] * (len(orig_list) - i)
        # Need to add the diverging part of dest_list.
        segments += dest_list[i:]
        if len(segments) == 0:
            # If they happen to be identical, use os.curdir.
            return path(os.curdir)
        else:
            return path(os.path.join(*segments))


    #@-node:ekr.20091204132801.2712:relpathto
    #@-node:ekr.20091204132801.6174:path strings...
    #@+node:ekr.20091204132801.6175:Listing, searching, walking, matching
    #@+node:ekr.20091204132801.2713:listdir
    def listdir(self, pattern=None):
        """ D.listdir() -> List of items in this directory.

        Use D.files() or D.dirs() instead if you want a listing
        of just files or just subdirectories.

        The elements of the list are path objects.

        With the optional 'pattern' argument, this only lists
        items whose names match the given pattern.
        """
        names = os.listdir(self)
        if pattern is not None:
            names = fnmatch.filter(names, pattern)
        return [self / child for child in names]

    #@-node:ekr.20091204132801.2713:listdir
    #@+node:ekr.20091204132801.2714:dirs
    def dirs(self, pattern=None):
        """ D.dirs() -> List of this directory's subdirectories.

        The elements of the list are path objects.
        This does not walk recursively into subdirectories
        (but see path.walkdirs).

        With the optional 'pattern' argument, this only lists
        directories whose names match the given pattern.  For
        example, d.dirs('build-*').
        """
        return [p for p in self.listdir(pattern) if p.isdir()]

    #@-node:ekr.20091204132801.2714:dirs
    #@+node:ekr.20091204132801.2715:files
    def files(self, pattern=None):
        """ D.files() -> List of the files in this directory.

        The elements of the list are path objects.
        This does not walk into subdirectories (see path.walkfiles).

        With the optional 'pattern' argument, this only lists files
        whose names match the given pattern.  For example,
        d.files('*.pyc').
        """

        return [p for p in self.listdir(pattern) if p.isfile()]

    #@-node:ekr.20091204132801.2715:files
    #@+node:ekr.20091204132801.2716:walk
    def walk(self, pattern=None):
        """ D.walk() -> iterator over files and subdirs, recursively.

        The iterator yields path objects naming each child item of
        this directory and its descendants.  This requires that
        D.isdir().

        This performs a depth-first traversal of the directory tree.
        Each directory is returned just before all its children.
        """
        for child in self.listdir():
            if pattern is None or child.fnmatch(pattern):
                yield child
            if child.isdir():
                for item in child.walk(pattern):
                    yield item

    #@-node:ekr.20091204132801.2716:walk
    #@+node:ekr.20091204132801.2717:walkdirs
    def walkdirs(self, pattern=None):
        """ D.walkdirs() -> iterator over subdirs, recursively.

        With the optional 'pattern' argument, this yields only
        directories whose names match the given pattern.  For
        example, mydir.walkdirs('*test') yields only directories
        with names ending in 'test'.
        """
        for child in self.dirs():
            if pattern is None or child.fnmatch(pattern):
                yield child
            for subsubdir in child.walkdirs(pattern):
                yield subsubdir

    #@-node:ekr.20091204132801.2717:walkdirs
    #@+node:ekr.20091204132801.2718:walkfiles
    def walkfiles(self, pattern=None):
        """ D.walkfiles() -> iterator over files in D, recursively.

        The optional argument, pattern, limits the results to files
        with names that match the pattern.  For example,
        mydir.walkfiles('*.tmp') yields only files with the .tmp
        extension.
        """
        for child in self.listdir():
            if child.isfile():
                if pattern is None or child.fnmatch(pattern):
                    yield child
            elif child.isdir():
                for f in child.walkfiles(pattern):
                    yield f

    #@-node:ekr.20091204132801.2718:walkfiles
    #@+node:ekr.20091204132801.2719:fnmatch
    def fnmatch(self, pattern):
        """ Return True if self.name matches the given pattern.

        pattern - A filename pattern with wildcards,
            for example '*.py'.
        """
        return fnmatch.fnmatch(self.name, pattern)

    #@-node:ekr.20091204132801.2719:fnmatch
    #@+node:ekr.20091204132801.2720:glob
    def glob(self, pattern):
        """ Return a list of path objects that match the pattern.

        pattern - a path relative to this directory, with wildcards.

        For example, path('/users').glob('*/bin/*') returns a list
        of all the files users have in their bin directories.
        """
        return map(path, glob.glob(_base(self / pattern)))


    #@-node:ekr.20091204132801.2720:glob
    #@-node:ekr.20091204132801.6175:Listing, searching, walking, matching
    #@+node:ekr.20091204132801.6176:Reading or writing and entire file
    #@+node:ekr.20091204132801.2721:open
    # --- Reading or writing an entire file at once.

    def open(self, mode='r'):
        """ Open this file.  Return a file object. """
        return file(self, mode)

    #@-node:ekr.20091204132801.2721:open
    #@+node:ekr.20091204132801.2722:bytes
    def bytes(self):
        """ Open this file, read all bytes, return them as a string. """
        f = self.open('rb')
        try:
            return f.read()
        finally:
            f.close()

    #@-node:ekr.20091204132801.2722:bytes
    #@+node:ekr.20091204132801.2723:write_bytes
    def write_bytes(self, bytes, append=False):
        """ Open this file and write the given bytes to it.

        Default behavior is to overwrite any existing file.
        Call this with write_bytes(bytes, append=True) to append instead.
        """
        if append:
            mode = 'ab'
        else:
            mode = 'wb'
        f = self.open(mode)
        try:
            f.write(bytes)
        finally:
            f.close()

    #@-node:ekr.20091204132801.2723:write_bytes
    #@+node:ekr.20091204132801.2724:text
    def text(self, encoding=None, errors='strict'):
        """ Open this file, read it in, return the content as a string.

        This uses 'U' mode in Python 2.3 and later, so '\r\n' and '\r'
        are automatically translated to '\n'.

        Optional arguments:

        encoding - The Unicode encoding (or character set) of
            the file.  If present, the content of the file is
            decoded and returned as a unicode object; otherwise
            it is returned as an 8-bit str.
        errors - How to handle Unicode errors; see help(str.decode)
            for the options.  Default is 'strict'.
        """
        if encoding is None:
            # 8-bit
            f = self.open(_textmode)
            try:
                return f.read()
            finally:
                f.close()
        else:
            # Unicode
            f = codecs.open(self, 'r', encoding, errors)
            # (Note - Can't use 'U' mode here, since codecs.open
            # doesn't support 'U' mode, even in Python 2.3.)
            try:
                t = f.read()
            finally:
                f.close()

            if isPython3:
                f = str
            else:
                f = unicode

            return (
                t.replace(f('\r\n'), f('\n')).
                replace(f('\r\x85'), f('\n')).
                replace(f('\r'), f('\n')).
                replace(f('\x85'), f('\n')).
                replace(f('\u2028'), f('\n'))
            )

            # return (t.replace(u'\r\n', u'\n')
                     # .replace(u'\r\x85', u'\n')
                     # .replace(u'\r', u'\n')
                     # .replace(u'\x85', u'\n')
                     # .replace(u'\u2028', u'\n'))

    #@-node:ekr.20091204132801.2724:text
    #@+node:ekr.20091204132801.2725:write_text
    def write_text(self, text, encoding=None, errors='strict', linesep=os.linesep, append=False):
        """ Write the given text to this file.

        The default behavior is to overwrite any existing file;
        to append instead, use the 'append=True' keyword argument.

        There are two differences between path.write_text() and
        path.write_bytes(): newline handling and Unicode handling.
        See below.

        Parameters:

          - text - str/unicode - The text to be written.

          - encoding - str - The Unicode encoding that will be used.
            This is ignored if 'text' isn't a Unicode string.

          - errors - str - How to handle Unicode encoding errors.
            Default is 'strict'.  See help(unicode.encode) for the
            options.  This is ignored if 'text' isn't a Unicode
            string.

          - linesep - keyword argument - str/unicode - The sequence of
            characters to be used to mark end-of-line.  The default is
            os.linesep.  You can also specify None; this means to
            leave all newlines as they are in 'text'.

          - append - keyword argument - bool - Specifies what to do if
            the file already exists (True: append to the end of it;
            False: overwrite it.)  The default is False.


        --- Newline handling.

        write_text() converts all standard end-of-line sequences
        ('\n', '\r', and '\r\n') to your platform's default end-of-line
        sequence (see os.linesep; on Windows, for example, the
        end-of-line marker is '\r\n').

        If you don't like your platform's default, you can override it
        using the 'linesep=' keyword argument.  If you specifically want
        write_text() to preserve the newlines as-is, use 'linesep=None'.

        This applies to Unicode text the same as to 8-bit text, except
        there are three additional standard Unicode end-of-line sequences:
        u'\x85', u'\r\x85', and u'\u2028'.

        (This is slightly different from when you open a file for
        writing with fopen(filename, "w") in C or file(filename, 'w')
        in Python.)


        --- Unicode

        If 'text' isn't Unicode, then apart from newline handling, the
        bytes are written verbatim to the file.  The 'encoding' and
        'errors' arguments are not used and must be omitted.

        If 'text' is Unicode, it is first converted to bytes using the
        specified 'encoding' (or the default encoding if 'encoding'
        isn't specified).  The 'errors' argument applies only to this
        conversion.

        """
        if isinstance(text, unicode):
            if linesep is not None:
                # Convert all standard end-of-line sequences to
                # ordinary newline characters.
                text = (
                    text.replace(f('\r\n'), f('\n')).
                    replace(f('\r\x85'), f('\n')).
                    replace(f('\r'), f('\n')).
                    replace(f('\x85'), f('\n')).
                    replace(f('\u2028'), f('\n'))
                )
                # text = (text.replace(u'\r\n', u'\n')
                            # .replace(u'\r\x85', u'\n')
                            # .replace(u'\r', u'\n')
                            # .replace(u'\x85', u'\n')
                            # .replace(u'\u2028', u'\n'))
                # text = text.replace(u'\n', linesep)
                text = text.replace(f('\n'),linesep)
            if encoding is None:
                encoding = sys.getdefaultencoding()
            bytes = text.encode(encoding, errors)
        else:
            # It is an error to specify an encoding if 'text' is
            # an 8-bit string.
            assert encoding is None

            if linesep is not None:
                text = (text.replace('\r\n', '\n')
                            .replace('\r', '\n'))
                bytes = text.replace('\n', linesep)

        self.write_bytes(bytes, append)

    #@-node:ekr.20091204132801.2725:write_text
    #@+node:ekr.20091204132801.2726:lines
    def lines(self, encoding=None, errors='strict', retain=True):
        """ Open this file, read all lines, return them in a list.

        Optional arguments:
            encoding - The Unicode encoding (or character set) of
                the file.  The default is None, meaning the content
                of the file is read as 8-bit characters and returned
                as a list of (non-Unicode) str objects.
            errors - How to handle Unicode errors; see help(str.decode)
                for the options.  Default is 'strict'
            retain - If true, retain newline characters; but all newline
                character combinations ('\r', '\n', '\r\n') are
                translated to '\n'.  If false, newline characters are
                stripped off.  Default is True.

        This uses 'U' mode in Python 2.3 and later.
        """
        if encoding is None and retain:
            f = self.open(_textmode)
            try:
                return f.readlines()
            finally:
                f.close()
        else:
            return self.text(encoding, errors).splitlines(retain)

    #@-node:ekr.20091204132801.2726:lines
    #@+node:ekr.20091204132801.2727:write_lines
    def write_lines(self, lines, encoding=None, errors='strict',
                    linesep=os.linesep, append=False):
        """ Write the given lines of text to this file.

        By default this overwrites any existing file at this path.

        This puts a platform-specific newline sequence on every line.
        See 'linesep' below.

        lines - A list of strings.

        encoding - A Unicode encoding to use.  This applies only if
            'lines' contains any Unicode strings.

        errors - How to handle errors in Unicode encoding.  This
            also applies only to Unicode strings.

        linesep - The desired line-ending.  This line-ending is
            applied to every line.  If a line already has any
            standard line ending ('\r', '\n', '\r\n', u'\x85',
            u'\r\x85', u'\u2028'), that will be stripped off and
            this will be used instead.  The default is os.linesep,
            which is platform-dependent ('\r\n' on Windows, '\n' on
            Unix, etc.)  Specify None to write the lines as-is,
            like file.writelines().

        Use the keyword argument append=True to append lines to the
        file.  The default is to overwrite the file.  Warning:
        When you use this with Unicode data, if the encoding of the
        existing data in the file is different from the encoding
        you specify with the encoding= parameter, the result is
        mixed-encoding data, which can really confuse someone trying
        to read the file later.
        """
        if append:
            mode = 'ab'
        else:
            mode = 'wb'
        f = self.open(mode)
        try:
            for line in lines:
                isUnicode = isinstance(line, unicode)
                if linesep is not None:
                    # Strip off any existing line-end and add the
                    # specified linesep string.
                    if isPython3:
                        f = str
                    else:
                        f = unicode
                    if isUnicode:
                        if line[-2:] in (
                            f('\r\n'), f('\x0d\x85')
                        ):
                            line = line[:-2]
                        elif line[-1:] in (
                            f('\r'), f('\n'),f('\x85'), f('\u2028')
                        ):
                            line = line[:-1]
                    else:
                        if line[-2:] == '\r\n':
                            line = line[:-2]
                        elif line[-1:] in ('\r', '\n'):
                            line = line[:-1]
                    line += linesep
                if isUnicode:
                    if encoding is None:
                        encoding = sys.getdefaultencoding()
                    line = line.encode(encoding, errors)
                f.write(line)
        finally:
            f.close()


    #@-node:ekr.20091204132801.2727:write_lines
    #@-node:ekr.20091204132801.6176:Reading or writing and entire file
    #@+node:ekr.20091204132801.6177:Querying the file system
    #@+node:ekr.20091204132801.2728:access
    # --- Methods for querying the filesystem.

    exists = os.path.exists
    isabs = os.path.isabs
    isdir = os.path.isdir
    isfile = os.path.isfile
    islink = os.path.islink
    ismount = os.path.ismount

    if hasattr(os.path, 'samefile'):
        samefile = os.path.samefile

    getatime = os.path.getatime
    atime = property(
        getatime, None, None,
        """ Last access time of the file. """)

    getmtime = os.path.getmtime
    mtime = property(
        getmtime, None, None,
        """ Last-modified time of the file. """)

    if hasattr(os.path, 'getctime'):
        getctime = os.path.getctime
        ctime = property(
            getctime, None, None,
            """ Creation time of the file. """)

    getsize = os.path.getsize
    size = property(
        getsize, None, None,
        """ Size of the file, in bytes. """)

    if hasattr(os, 'access'):
        def access(self, mode):
            """ Return true if current user has access to this path.

            mode - One of the constants os.F_OK, os.R_OK, os.W_OK, os.X_OK
            """
            return os.access(self, mode)

    #@-node:ekr.20091204132801.2728:access
    #@+node:ekr.20091204132801.2729:stat
    def stat(self):
        """ Perform a stat() system call on this path. """
        return os.stat(self)

    #@-node:ekr.20091204132801.2729:stat
    #@+node:ekr.20091204132801.2730:lstat
    def lstat(self):
        """ Like path.stat(), but do not follow symbolic links. """
        return os.lstat(self)

    #@-node:ekr.20091204132801.2730:lstat
    #@+node:ekr.20091204132801.2731:statvfs
    if hasattr(os, 'statvfs'):
        def statvfs(self):
            """ Perform a statvfs() system call on this path. """
            return os.statvfs(self)

    #@-node:ekr.20091204132801.2731:statvfs
    #@+node:ekr.20091204132801.2732:pathconf
    if hasattr(os, 'pathconf'):
        def pathconf(self, name):
            return os.pathconf(self, name)


    #@-node:ekr.20091204132801.2732:pathconf
    #@-node:ekr.20091204132801.6177:Querying the file system
    #@+node:ekr.20091204132801.6178:Modifying files and directories
    #@+node:ekr.20091204132801.2733:utime
    # --- Modifying operations on files and directories

    def utime(self, times):
        """ Set the access and modified times of this file. """
        os.utime(self, times)

    #@-node:ekr.20091204132801.2733:utime
    #@+node:ekr.20091204132801.2734:chmod
    def chmod(self, mode):
        os.chmod(self, mode)

    #@-node:ekr.20091204132801.2734:chmod
    #@+node:ekr.20091204132801.2735:chown
    if hasattr(os, 'chown'):
        def chown(self, uid, gid):
            os.chown(self, uid, gid)

    #@-node:ekr.20091204132801.2735:chown
    #@+node:ekr.20091204132801.2736:rename
    def rename(self, new):
        os.rename(self, new)

    #@-node:ekr.20091204132801.2736:rename
    #@+node:ekr.20091204132801.2737:renames
    def renames(self, new):
        os.renames(self, new)


    #@-node:ekr.20091204132801.2737:renames
    #@-node:ekr.20091204132801.6178:Modifying files and directories
    #@+node:ekr.20091204132801.6179:Create/delete directories
    #@+node:ekr.20091204132801.2738:mkdir
    # --- Create/delete operations on directories

    def mkdir(self, mode=0o777):
        os.mkdir(self, mode)

    #@-node:ekr.20091204132801.2738:mkdir
    #@+node:ekr.20091204132801.2739:makedirs
    def makedirs(self, mode=0o777):
        os.makedirs(self, mode)

    #@-node:ekr.20091204132801.2739:makedirs
    #@+node:ekr.20091204132801.2740:rmdir
    def rmdir(self):
        os.rmdir(self)

    #@-node:ekr.20091204132801.2740:rmdir
    #@+node:ekr.20091204132801.2741:removedirs
    def removedirs(self):
        os.removedirs(self)


    #@-node:ekr.20091204132801.2741:removedirs
    #@-node:ekr.20091204132801.6179:Create/delete directories
    #@+node:ekr.20091204132801.6180:Modifying files
    #@+node:ekr.20091204132801.2742:touch
    # --- Modifying operations on files

    def touch(self):
        """ Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        fd = os.open(self, os.O_WRONLY | os.O_CREAT, 0o666)
        os.close(fd)
        os.utime(self, None)

    #@-node:ekr.20091204132801.2742:touch
    #@+node:ekr.20091204132801.2743:remove
    def remove(self):
        os.remove(self)

    #@-node:ekr.20091204132801.2743:remove
    #@+node:ekr.20091204132801.2744:unlink
    def unlink(self):
        os.unlink(self)


    #@-node:ekr.20091204132801.2744:unlink
    #@-node:ekr.20091204132801.6180:Modifying files
    #@+node:ekr.20091204132801.6181:Links...
    #@+node:ekr.20091204132801.2745:link
    # --- Links

    if hasattr(os, 'link'):
        def link(self, newpath):
            """ Create a hard link at 'newpath', pointing to this file. """
            os.link(self, newpath)

    #@-node:ekr.20091204132801.2745:link
    #@+node:ekr.20091204132801.2746:symlink
    if hasattr(os, 'symlink'):
        def symlink(self, newlink):
            """ Create a symbolic link at 'newlink', pointing here. """
            os.symlink(self, newlink)

    #@-node:ekr.20091204132801.2746:symlink
    #@+node:ekr.20091204132801.2747:readlink
    if hasattr(os, 'readlink'):
        def readlink(self):
            """ Return the path to which this symbolic link points.

            The result may be an absolute or a relative path.
            """
            return path(os.readlink(self))

        def readlinkabs(self):
            """ Return the path to which this symbolic link points.

            The result is always an absolute path.
            """
            p = self.readlink()
            if p.isabs():
                return p
            else:
                return (self.parent / p).abspath()


    #@-node:ekr.20091204132801.2747:readlink
    #@-node:ekr.20091204132801.6181:Links...
    #@+node:ekr.20091204132801.6182:High-level operations from shutil
    #@+node:ekr.20091204132801.2748:chroot
    # --- High-level functions from shutil

    copyfile = shutil.copyfile
    copymode = shutil.copymode
    copystat = shutil.copystat
    copy = shutil.copy
    copy2 = shutil.copy2
    copytree = shutil.copytree
    if hasattr(shutil, 'move'):
        move = shutil.move
    rmtree = shutil.rmtree


    # --- Special stuff from os

    if hasattr(os, 'chroot'):
        def chroot(self):
            os.chroot(self)

    #@-node:ekr.20091204132801.2748:chroot
    #@+node:ekr.20091204132801.2749:startfile
    if hasattr(os, 'startfile'):
        def startfile(self):
            os.startfile(self)

    #@-node:ekr.20091204132801.2749:startfile
    #@-node:ekr.20091204132801.6182:High-level operations from shutil
    #@-others
#@-node:ekr.20091204132801.2687:class path
#@-others
#@-node:ekr.20091204131831.6103:@thin ../external/path.py
#@-leo
