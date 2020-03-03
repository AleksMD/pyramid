<%inherit file="layout.mako"/>
<%block name="subtitle">Login -</%block>
<%block name="content">
<p><strong>Login</strong><br>
${message}
</p>
<form action="${url}" style="color: black;" method="post">
<input type="hidden" name="next" value="${next_url}"/>
<div class="form-group">
    <label for="login">Username</label>
    <input type="text" name="login" value="${login}">
</div>
<div class="form-group">
    <label for="password">Password</label>
    <input type="password" name="password">
</div>
<div class="form-group">
    <button type="submit" name="form.submitted" value="Log In" class="btn
    btn-default">Log In</button>
</div>
</form>
</%block>
