
__all__ = ['language']

# Switch to date based version
__version__ = "24.2.0"

# Track probable issues like setting attribute that is not referenced.
# Set to true to make StringTemplate check your work as it evaluates templates.
# Problems are sent to error listener.
# Currently, warns when you set attributes that are not used.
lintMode = False

# If you want parse errors to propagate all the way up to the caller.
# Primarily here to improve unit testing.
crashOnActionParseError = False

from stringtemplate3.errors import *
from stringtemplate3.writers import *
from stringtemplate3.templates import *
from stringtemplate3.groups import *
from stringtemplate3.interfaces import *
from stringtemplate3.grouploaders import *


