from wallstreet.wallstreet import Stock, Call, Put

__all__ = ['Stock', 'Call', 'Put']

def get_version_from_pyproject():
    version_line_prefix = 'version ='
    with open('pyproject.toml', 'r') as file:
        for line in file:
            if line.strip().startswith(version_line_prefix):
                # Extract the version part and remove quotes
                version = line.split('=')[1].strip().strip('"').strip("'")
                return version
    return "unknown"

__version__ = get_version_from_pyproject()