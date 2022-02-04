try:
    file = open('.version', 'r')
except FileNotFoundError:
    version = ''
else:
    version = file.read().strip()


if not version:
    version = "<development>"
