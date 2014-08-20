from html.parser import HTMLParser

def decomment(html):
    """Given a string of HTML content, return the HTML with all HTML
    comments removed.
    """

    out = ""
    parser = CommentEater()
    for line in html.split('\n'):
        parser.feed(line)
        out += parser.buffer + '\n'
        parser.buffer = ""

    return out


def _to_html_attrs(attrs):
    attrlist = ['{}="{}"'.format(k, v) for (k, v) in attrs]
    return ' '.join(attrlist)


class CommentEater(HTMLParser):

    def __init__(self):
        super().__init__()
        self.buffer = ""


    def handle_starttag(self, tag, attrs):
        if not attrs:
            self.buffer += "<{}>".format(tag)
        else:
            self.buffer += "<{} {}>".format(tag, _to_html_attrs(attrs))


    def handle_endtag(self, tag):
        self.buffer += "</{}>".format(tag)


    def handle_startendtag(self, tag, attrs):
        if not attrs:
            self.buffer += "<{} />".format(tag)
        else:
            self.buffer += "<{} {} />".format(tag, _to_html_attrs(attrs))


    def handle_data(self, data):
        self.buffer += data


    def handle_entityref(self, name):
        self.buffer += "&{};".format(name)


    def handle_charref(self, name):
        self.handle_entityref('#' + name)


    # where the magic happens!
    def handle_comment(self, data):
        return


    def handle_decl(self, decl):
        self.buffer += "<!{}>".format(decl)


    def handle_pi(self, data):
        self.buffer += "<?{}>".format(data)


    def unknown_decl(self, data):
        self.buffer += "<![{}]>".format(data)



