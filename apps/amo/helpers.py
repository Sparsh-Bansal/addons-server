import collections

from django.utils import translation
from django.utils.translation import ugettext as _

from babel import Locale
from babel.support import Format
import jinja2

from jingo import register, env

import amo
from addons.models import Category


@register.filter
def paginator(pager):
    return Paginator(pager).render()


@register.function
def is_mobile(app):
    return app == amo.MOBILE


@register.function
def sidebar(app):
    """Populates the sidebar with (categories, types)."""
    if app is None:
        return [], []

    q = Category.objects.filter(application=app.id, weight__gte=0,
                                addontype=amo.ADDON_EXTENSION)
    _categories = list(q)

    # Plugins are on a static page, so we add it to categories dynamically.
    # There are 7 plugins, so we hardcode the number.  That's fantastic.
    if amo.ADDON_PLUGIN in app.types:
        # Use a namedtuple instead of the Category class so Translations aren't
        # triggered.
        _Category = collections.namedtuple('Category', 'name weight count')
        _categories.append(_Category(name=_('Plugins'), weight=0, count=7))
    categories = sorted(_categories, key=lambda x: (x.weight, x.name))

    Type = collections.namedtuple('Type', 'name url')
    types = [Type(_('Collections'), '/collections')]
    shown_types = [amo.ADDON_PERSONA, amo.ADDON_DICT, amo.ADDON_SEARCH,
                   amo.ADDON_THEME]
    for type_ in shown_types:
        if type_ in app.types:
            name = amo.ADDON_TYPES[type_]
            types.append(Type(name, '#' + name))

    return categories, types


class Paginator(object):

    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) / 2

        self.page = pager.number
        self.num_pages = pager.paginator.num_pages
        self.count = pager.paginator.count

        pager.page_range = self.range()
        pager.dotted_upper = self.count not in pager.page_range
        pager.dotted_lower = 1 not in pager.page_range

    def range(self):
        """Return a list of page numbers to show in the paginator."""
        page, total, span = self.page, self.num_pages, self.span
        if total < self.max:
            lower, upper = 0, total
        elif page < span + 1:
            lower, upper = 0, span * 2
        elif page > total - span:
            lower, upper = total - span * 2, total
        else:
            lower, upper = page - span, page + span - 1
        return range(max(lower + 1, 1), min(total, upper) + 1)

    def render(self):
        c = {'pager': self.pager, 'num_pages': self.num_pages,
             'count': self.count}
        t = env.get_template('amo/paginator.html').render(**c)
        return jinja2.Markup(t)


def _get_format():
    lang = translation.get_language()
    locale = Locale(translation.to_locale(lang))
    return Format(locale)


@register.filter
def numberfmt(num, format=None):
    return _get_format().decimal(num, format)
