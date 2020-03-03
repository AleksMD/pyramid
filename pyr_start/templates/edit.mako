<%inherit file="layout.mako"/>
<%block name="subtitle">Edit ${pagename}</%block>
<%block name="content">
<p>
Editing <strong>${pagename}</strong>
</p>
<p> You can return to the
<a href="${request.route_url('view_page', pagename='FrontPage')}">Front
Page</a>.
</p>
<form action="${save_url}" method="post">
<div class="form-group">
<textarea class="form-control" name="body" cols="60" rows="10">${pagedata}</textarea>
</div>
<div class="form-group">
<button type="submit" name="form.submitted" value="Save" class="btn
btn-default">Save</button>
</div>
</form>
</%block>
