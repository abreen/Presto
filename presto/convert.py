"""This module provides all the string processing & substitution functionality
when a Markdown draft should be converted to HTML.
"""
from __future__ import print_function

import sys
import datetime
import re

from six.moves import cStringIO

import presto.functions as functions

TITLE_PATTERN = re.compile(r'{{\s*title\s*}}')
HEAD_PATTERN = re.compile(r'{{\s*head\s*}}')
FOOTER_PATTERN = re.compile(r'{{\s*footer\s*}}')
BODY_PATTERN = re.compile(r'{{\s*body\s*}}')

BRACE_PATTERN = re.compile(r'(\n[ \t]*)?{([{%])(.*?)[%}]}', re.DOTALL)
ESCAPE_PATTERN = re.compile(r'\\({|}|%)')
COMMENT_PATTERN = re.compile(r'(<!--.*?-->)', re.DOTALL)

TODAY = datetime.datetime.now().strftime('%B %e, %Y')
FOOTER = 'Last modified on ' + TODAY + '.'


def md_to_html(md, template_str, f):
    """Given a markdown.Markdown object, a string containing an HTML template,
    and a file object open for reading that corresponds to a file containing
    Markdown (with {% ... %} and/or {{ ... }} sequences), return an HTML string
    with the Markdown elements converted to HTML and the code within {% ... %}
    and {{ ... }} blocks evaluated.
    """
    content = f.read()

    # remove all HTML comments
    content = re.sub(COMMENT_PATTERN, '', content)

    # convert using the markdown.Markdown object, just to obtain metadata
    md.convert(content)
    metadata = md.Meta

    if 'title' not in metadata:
        return ('bad-metadata', 'draft has no title')

    if 'path' in metadata:
        # add directories to the Python module search path, so import
        # statements in {% ... %} sequences can work
        for d in metadata['path']:
            sys.path.append(d)

    locals_ = {}
    globals_ = {}
    errors = []

    # make the functions in the functions module available
    globals_.update(get_functions(functions))

    # make the metadata for this Markdown draft available
    for var, val in metadata.items():
        if len(val) == 1:
            globals_.update({var: str(val[0])})
        else:
            globals_.update({var: [str(s) for s in val]})

    # from top to bottom, evaluate {% ... %} and {{ ... }} sequences
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

        if kind == '%':
            # code block
            inner = dedent(inner, len(ws_before))

            try:
                exec(inner, globals_, locals_)
            except:
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__

                import traceback
                traceback.print_exc()

                errors.append(
                    ('%-error', 'error occurred evaluating {% ... %}')
                )

                return ''

            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

            if ws_before:
                return '\n' + ws_before + indent(out_.getvalue(), ws_before)
            else:
                return indent(out_.getvalue(), ws_before)

        else: # kind == '{'
            # eval of a function call/variable
            inner = inner.strip()

            try:
                rv = eval(inner, globals_, locals_)
            except:
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__

                import traceback
                traceback.print_exc()

                errors.append(
                    ('{-error', 'error occurred evaluating {{ ... }}')
                )

                return ''

            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

            if ws_before:
                return '\n' + ws_before + repr(rv)
            else:
                return repr(rv)

    content = re.sub(BRACE_PATTERN, sub, content)

    if errors:
        return errors[0]

    # replace occurrences of '\{', '\}' and '\%' with just '{', etc.
    def deescape(match):
        return match.group(1)

    content = re.sub(ESCAPE_PATTERN, deescape, content)

    # convert body from Markdown to HTML
    md.reset()
    content = md.convert(content)

    # substitute {{ title }}, {{ head }}, {{ body }} and {{ footer }} in the template

    # why we use a function as the "repl" argument and not just the string:
    # if the page content contains substrings that look like backreferences
    # (e.g., \1) or group references (\gfoo), this can mess up the
    # substitution; by using a function instead, the string we return as a
    # replacement will not be scanned for these substrings
    content = re.sub(BODY_PATTERN, lambda _: content, template_str)

    content = re.sub(TITLE_PATTERN, metadata['title'][0], content)

    if 'head' in metadata:
        head_lines = '\n'.join(metadata['head'])
    else:
        head_lines = ''

    content = re.sub(HEAD_PATTERN, head_lines, content)

    content = re.sub(FOOTER_PATTERN, FOOTER, content)

    return content


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
