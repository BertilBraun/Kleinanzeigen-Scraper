def to_lower_snake_case(s: str) -> str:
    # replace all uppercase letters with _ and lowercase
    return ''.join(['_' + c.lower() if c.isupper() else c for c in s]).lstrip('_')


def to_readable_name(s: str) -> str:
    # replace all _ with space and capitalize first letter of each word (i.e. full_rig -> Full Rig)
    # also split by uppercase letters (i.e. mastLength -> Mast Length)
    return ' '.join([word.capitalize() for word in to_lower_snake_case(s).split('_')])


def indent(s: str, spaces: int = 2) -> str:
    return '\n'.join(' ' * spaces + line for line in s.splitlines())


def parse_numeric(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value
