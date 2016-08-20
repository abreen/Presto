"""This module provides all the string processing & substitution functionality
when a Markdown draft should be converted to HTML.
"""
from __future__ import print_function

import sys
import datetime
import re

import six
from six.moves import cStringIO

import presto.functions as functions
import presto.options as options
import presto.config as config
import presto.output as output

BRACE_PATTERN = re.compile(r'(\n[ \t]*)?{([~=!])(.*?)\2}', re.DOTALL)
ESCAPE_PATTERN = re.compile(r'\\([{}~=!])')
COMMENT_PATTERN = re.compile(r'(<!--.*?-->)', re.DOTALL)


class BracketError(ValueError):
    pass


def eval_brackets(s, errors, locals_, globals_):
    def sub(match):
        ws_before = match.group(1)
        kind = match.group(2)
        inner = match.group(3)

        if ws_before:
            # remove leading \n
            ws_before = ws_before[1:]
        else:
            ws_before = ''

        in_, out_ = cStringIO(), cStringIO()
        sys.stdin = in_
        sys.stdout = out_

        if kind == '!':
            # code block
            inner = dedent(inner, len(ws_before))

            try:
                six.exec_(inner, globals_, locals_)
            except Exception as e:
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__

                import traceback
                e_type, e_value, e_tb = sys.exc_info()
                e_str = traceback.format_exception(e_type, e_value, None, 0)[0].strip()

                errors.append('error occurred executing {! ... !}: ' + e_str)

                if options.get('debug'):
                    output.traceback()

                if options.get('use_empty'):
                    return ''
                else:
                    raise BracketError

            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

            if ws_before:
                return '\n' + ws_before + indent(out_.getvalue(), ws_before)
            else:
                return indent(out_.getvalue(), ws_before)

        elif kind in ['~', '=']:
            # evaluating an expression
            inner = inner.strip()

            try:
                rv = eval(inner, globals_, locals_)
            except Exception as e:
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__

                import traceback
                e_type, e_value, e_tb = sys.exc_info()
                e_str = traceback.format_exception(e_type, e_value, None, 0)[0].strip()

                if kind == '~':
                    errors.append('error occurred evaluating {~ ... ~}: ' + e_str)
                elif kind == '=':
                    errors.append('error occurred evaluating {= ... =}: ' + e_str)

                if options.get('debug'):
                    output.traceback()

                if options.get('use_empty'):
                    return ''
                else:
                    raise BracketError

                return ''

            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

            if kind == '~':
                str_out = repr(rv)
            elif kind == '=':
                # unicode() in Python 2, str() in Python 3
                str_out = six.text_type(rv)

            if ws_before:
                return '\n' + ws_before + str_out
            else:
                return str_out

    # from top to bottom, evaluate {-sequences using above function
    try:
        s_evald = re.sub(BRACE_PATTERN, sub, s)
    except BracketError:
        return None

    return s_evald


def md_to_html(md, template_str, f):
    """Given a markdown.Markdown object, a string containing an HTML template,
    and a file object open for reading that corresponds to a file containing
    Markdown (with {-sequences), return an HTML string with the Markdown
    elements converted to HTML and the code within the {-sequences executed.
    """
    body_md = f.read()

    # remove all HTML comments
    body_md = re.sub(COMMENT_PATTERN, '', body_md)

    # convert using the markdown.Markdown object, just to obtain metadata
    md.convert(body_md)
    metadata = md.Meta

    if 'path' in metadata:
        # add directories to the Python module search path, so import
        # statements in {%-sequences can work
        for d in metadata['path']:
            sys.path.append(d)

    # in Python 2, the variable names and value(s) are unicode(), since they
    # come from Python-Markdown that way; we will use str() convert them to
    # regular strings and accept the fact that non-ASCII characters in them
    # will produce an issue (in Python 3 this does nothing)
    new_metadata = {}
    for var, val in metadata.items():
        if len(val) == 1:
            # e.g., foo: bar (only one value for the variable "foo")
            new_metadata.update({str(var): str(val[0])})
        else:
            new_metadata.update({str(var): [str(s) for s in val]})

    globals_ = {}
    locals_ = {}
    errors = []

    # make the variables defined in the config file available
    globals_.update(config.get_variables())

    # make the functions in the functions module available
    globals_.update(get_functions(functions))

    draft_metadata = {var: val for var, val in new_metadata.items()}

    # make the metadata available under "metadata"
    globals_.update({'metadata': draft_metadata})

    # make each metadata variable available
    globals_.update(draft_metadata)

    body_md_evald = eval_brackets(body_md, errors, globals_, locals_)

    if body_md_evald is None:
        return None, errors

    # convert body from Markdown to HTML
    md.reset()
    body_html = md.convert(body_md_evald)

    globals_.update({'content': body_html})

    page_evald = eval_brackets(template_str, errors, globals_, locals_)

    if page_evald is None:
        return None, errors

    # remove backslash from occurrences of '\{', '\}', etc.
    def deescape(match):
        return match.group(1)

    page_evald_deescaped = re.sub(ESCAPE_PATTERN, deescape, page_evald)

    return page_evald_deescaped, errors


def get_functions(mod):
    import inspect

    funcs = {}
    for name, member in inspect.getmembers(mod):
        if inspect.isfunction(member):
            funcs[name] = member

    return funcs


def dedent(code, n):
    """Given a string representing several lines of code, where the the first
    non-empty line of code is preceded with n spaces or tabs, return the code
    string with the first n spaces or tabs of every line removed.
    """
    lines = code.split('\n')

    if len(lines) == 1:
        return code.strip()

    new_lines = []
    for line in lines:
        if not line:
            new_lines.append('')
        else:
            new_lines.append(line[n:])

    new_code = '\n'.join(new_lines)
    return new_code


def indent(code, before):
    lines = code.split('\n')

    if len(lines) == 1:
        return code

    new_lines = [lines[0]]
    for line in lines[1:]:
        new_lines.append(before + line)

    return '\n'.join(new_lines)
