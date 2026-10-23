"""Local regression checks for the remembered-device authentication flow."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from remembered_login import issue_token, valid_token, password_tag


class Stop(Exception): pass
class Rerun(Exception): pass


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.submitted = False
        self.entered = ''
        self.errors = []
    def caption(self, *a): pass
    def markdown(self, *a): pass
    def error(self, text): self.errors.append(text)
    def warning(self, text): self.errors.append(text)
    def stop(self): raise Stop()
    def rerun(self): raise Rerun()
    def form(self, *a): return self
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def text_input(self, *a, **kw): return self.entered
    def form_submit_button(self, *a, **kw): return self.submitted


class DeviceLoginTests(unittest.TestCase):
    def setUp(self):
        import hmac, secrets
        self.st = FakeStreamlit()
        self.browser = {'token': ''}
        self.answer = None
        def component(**kw):
            self.command = kw['command']
            return self.answer
        self.scope = dict(st=self.st, secrets=secrets, hmac=hmac,
                          _device_store=component, hero=lambda:None,
                          issue_token=issue_token, valid_token=valid_token,
                          password_tag=password_tag)
        tree = ast.parse(Path('seher_ui.py').read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and
                 n.name in ('device_command','sync_device','logout','login')]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'auth','exec'),self.scope)
        self.password = 'test-only-password'
    def login(self):
        self.scope['login']({'get_secret': lambda:self.password})
    def ack(self, error=False):
        c = self.command
        if not error:
            if c['action']=='save': self.browser['token']=c['token']
            elif c['action']=='clear': self.browser['token']=''
        self.answer = dict(revision=c['revision'], token=self.browser['token'] if not error else '', error=error)
    def ready(self):
        with self.assertRaises(Stop): self.login()
        self.ack()
    def test_new_browser_wrong_password_and_tampered_token(self):
        self.browser['token']=issue_token(self.password)[:-1]+'!'
        self.ready()
        self.st.submitted=True;self.st.entered='wrong'
        with self.assertRaises(Stop):self.login()
        self.assertFalse(self.st.session_state.get('authenticated'))
        self.assertTrue(self.st.errors)
    def test_password_login_browser_restart_and_logout(self):
        self.ready();self.st.submitted=True;self.st.entered=self.password
        with self.assertRaises(Rerun):self.login()
        # The read acknowledgement cannot satisfy the pending save operation.
        with self.assertRaises(Stop):self.login()
        self.ack();self.login()
        self.assertTrue(valid_token(self.browser['token'],self.password))
        # A fresh server session reads the same browser record, without a form.
        self.st.session_state.clear();self.st.submitted=False;self.answer=None
        self.ready();self.login()
        self.assertTrue(self.st.session_state['authenticated'])
        with self.assertRaises(Rerun):self.scope['logout']()
        # Stale component values cannot log the user back in during deletion.
        with self.assertRaises(Stop):self.login()
        self.ack()
        with self.assertRaises(Stop):self.login()
        self.assertEqual(self.browser['token'],'')
        self.assertFalse(self.st.session_state.get('authenticated'))
    def test_password_change_revokes_browser_and_active_session(self):
        self.browser['token']=issue_token(self.password)
        self.ready();self.login()
        self.password='changed-password'
        with self.assertRaises(Stop):self.login()
        self.assertFalse(self.st.session_state.get('authenticated'))
    def test_storage_blocked_still_allows_password_session(self):
        with self.assertRaises(Stop):self.login()
        self.ack(error=True);self.st.submitted=True;self.st.entered=self.password
        with self.assertRaises(Rerun):self.login()
        with self.assertRaises(Stop):self.login()
        self.ack(error=True);self.login()
        self.assertTrue(self.st.session_state['authenticated'])
    def test_cookie_restores_refresh_before_component_ready(self):
        token=issue_token(self.password)
        self.st.context=SimpleNamespace(cookies={'seher_auzef_device':token})
        self.login()
        self.assertTrue(self.st.session_state['authenticated'])
        with self.assertRaises(Rerun):self.scope['logout']()
        # Cookies on this WebSocket remain stale during browser deletion.
        with self.assertRaises(Stop):self.login()
        self.ack()
        with self.assertRaises(Stop):self.login()
        self.assertFalse(self.st.session_state.get('authenticated'))
    def test_cookie_with_wrong_signature_cannot_bootstrap(self):
        self.st.context=SimpleNamespace(cookies={'seher_auzef_device':issue_token('wrong-password')})
        with self.assertRaises(Stop):self.login()
        self.assertFalse(self.st.session_state.get('authenticated'))
    def test_independent_devices_and_token_integrity(self):
        a,b=issue_token(self.password),issue_token(self.password)
        self.assertNotEqual(a,b)
        for token in (a,b):self.assertTrue(valid_token(token,self.password))
        for token in (None,True,{},'',a+'.extra',a.replace('v1.','v2.'),a[:-2], 'x'*10000):
            self.assertFalse(valid_token(token,self.password))
        self.assertFalse(valid_token(a,'other-password'))


if __name__=='__main__': unittest.main(verbosity=2)
