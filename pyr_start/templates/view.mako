<%inherit file="layout.mako"/>
<%block name="subtitle">${page.name}</%block>
<%block name="content">
${page_body | n}
<p>
<a href="${edit_url}">Edit this page</a>
</p>
<p>
    Viewing <strong>${page.name}</strong>, created by
    <strong>${page.creator.name}</strong>.
</p>
<p> You can return to the
<a href="${request.route_url('view_page', pagename='FrontPage')}">Front
Page</a>.
</p>
</%block>
