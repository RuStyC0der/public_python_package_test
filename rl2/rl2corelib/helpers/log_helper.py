# Remove \n and a lot of spaces from query to logging
def prepare_query_to_log(query_):
    target = ' ' * 2
    s = query_.replace('\n', '').strip()
    while target in s:
        s = s.replace(target, ' ')
    return s
