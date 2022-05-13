from jinja2 import Template


class TemplateEngine:
    def __init__(self, tpl_path):
        self.tpl_path = tpl_path

    @staticmethod
    def bytes_to_str(bytes_int: int, unit=None):
        if unit:
            if unit == 'K':
                return '%.2f' % float(bytes_int / (1024 ** 1))
            elif unit == 'M':
                return '%.2f' % float(bytes_int / (1024 ** 2))
            elif unit == 'G':
                return '%.2f' % float(bytes_int / (1024 ** 3))
            elif unit == 'T':
                return '%.2f' % float(bytes_int / (1024 ** 4))
        else:
            return str(bytes)

    def render(self, **data):
        tpl_content = open(self.tpl_path).read()
        template = Template(tpl_content)
        return template.render(**data)
