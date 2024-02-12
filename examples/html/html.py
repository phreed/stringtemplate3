import os
import cgi
import stringtemplate3

# Define a template group.
# Templates will be loaded from the 'templates' directory.
group = stringtemplate3.StringTemplateGroup(
    name='default',
    rootDir=os.path.join(os.path.dirname(__file__), 'templates')
    )


# Define an attribute renderer that will escape any string in a HTML save
# way that is expanded with format="escape".
# See templage/page.st for an example
class EscapeRenderer(stringtemplate3.AttributeRenderer):
    def toString(self, o, formatName=None):
        if formatName is None:
            # no formatting specified
            return str(o)

        if formatName == "escape":
            return cgi.escape(str(o))
        else:
            raise ValueError("Unsupported format name")

group.registerRenderer(str, EscapeRenderer())

# Create an instance of the 'menu' template.
# This will be loaded from the file 'templates/menu.st'
menu = group.getInstanceOf('menu')

# Create some menu items and add them to the 'items' attribute of the menu
# Note that the second assignment to menu['items'] does not override the
# previous one, but appends a new item,
menuItem = group.getInstanceOf('menuItem')
menuItem['url'] = 'http://www.stringtemplate.org/'
menuItem['text'] = 'StringTemplate Homepage'
menu['items'] = menuItem

menuItem = group.getInstanceOf('menuItem')
menuItem['url'] = 'http://www.google.com/'
menuItem['text'] = 'Google'
menu['items'] = menuItem

# Load the body text from 'templates/page_index.st'
# Note the reference to title in the template!
body = group.getInstanceOf('page_index')

# Assemble complete HTML document
page = group.getInstanceOf('page')
page['title'] = "This is <just> a demo"
page['menu'] = menu
page['body'] = body

# At this point all templates are expanded. Because body is now a child of
# page, the title attribute from page can be expanded in the body template.
print page.toString()
