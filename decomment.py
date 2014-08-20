from html.parser import HTMLParser

def decomment(html):
    """Given a string of HTML content, return the HTML with all HTML
    comments removed.
    """

    string = ""
    parser = CommentEater()
    for line in html.split('\n'):
        string += parser.feed(html)

    return string


def _to_html_attrs(attrs):
    attrlist = ['{}="{}"'.format(k, v) for (k, v) in attrs]
    return ' '.join(attrlist)


class CommentEater(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if not attrs:
            print("<{}>".format(tag), end='')
        else:
            print("<{} {}>".format(tag, _to_html_attrs(attrs)), end='')

    def handle_endtag(self, tag):
        print("</{}>".format(tag), end='')

    def handle_startendtag(self, tag, attrs):
        if not attrs:
            print("<{} />".format(tag), end='')
        else:
            print("<{} {} />".format(tag, _to_html_attrs(attrs)), end='')

    def handle_data(self, data):
        print(data, end='')

    def handle_entityref(self, name):
        print("&{};".format(name), end='')

    def handle_charref(self, name):
        self.handle_entityref('#' + name)

    # where the magic happens!
    def handle_comment(self, data):
        print('', end='')

    def handle_decl(self, decl):
        print("<!{}>".format(decl), end='')

    def handle_pi(self, data):
        print("<?{}>".format(data), end='')

    def unknown_decl(self, data):
        print("<![{}]>".format(data), end='')

