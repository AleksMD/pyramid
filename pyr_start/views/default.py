from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.compat import escape
import re
from docutils.core import publish_parts
from ..tasks import greet_guest, serial_page

from .. import models

# regular expression used to find WikiWords
wikiwords = re.compile(r"\b([A-Z]\w+[A-Z]+\w+)")


@view_config(route_name='view_wiki')
def view_wiki(request):
    next_url = request.route_url('view_page', pagename='FrontPage')
    greet_guest.delay()
    return HTTPFound(location=next_url)


@view_config(route_name='view_page', renderer='../templates/view.mako',
             permission='view')
def view_page(request):
    page = request.context.page
    page_to_send = page._to_dict()
    serial_page.delay(page_to_send)

    def add_link(match):
        word = match.group(1)
        exists = request.dbsession.query(
            models.Page).filter_by(name=word).all()
        if exists:
            view_url = request.route_url('view_page', pagename=word)
            return f'<a href="{view_url}">{escape(word)}</a>'
        else:
            add_url = request.route_url('add_page', pagename=word)
            return f'<a href="{add_url}">{escape(word)}</a>'

    content = publish_parts(page.data, writer_name='html')['html_body']
    content = wikiwords.sub(add_link, content)
    edit_url = request.route_url('edit_page', pagename=page.name)
    response = dict(page=page, page_body=content, edit_url=edit_url)
    return response


@view_config(route_name='edit_page', renderer='../templates/edit.mako',
             permission='edit')
def edit_page(request):
    page = request.context.page
    if 'form.submitted' in request.params:
        page.data = request.params['body']
        next_url = request.route_url('view_page', pagename=page.name)
        return HTTPFound(location=next_url)
    return dict(
        pagename=page.name,
        pagedata=page.data,
        save_url=request.route_url('edit_page', pagename=page.name))


@view_config(route_name='add_page', renderer='../templates/edit.mako',
             permission='create')
def add_page(request):
    pagename = request.context.pagename
    if 'form.submitted' in request.params:
        body = request.params['body']
        page = models.Page(name=pagename, data=body)
        page.creator = request.user
        request.dbsession.add(page)
        next_url = request.route_url('view_page', pagename=pagename)
        return HTTPFound(location=next_url)
    save_url = request.route_url('add_page', pagename=pagename)
    return dict(pagename=pagename, pagedata='', save_url=save_url)
