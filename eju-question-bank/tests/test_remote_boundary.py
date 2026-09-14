import http.client
import json
import threading
import pytest
from eju_bank.server import create_server
from eju_bank.errors import SecurityError


def test_bad_remote_configuration_fails_before_binding(tmp_path):
    with pytest.raises(SecurityError): create_server(tmp_path/'db',host='0.0.0.0',port=0)
    with pytest.raises(SecurityError): create_server(tmp_path/'db',allow_remote=True,port=0)
    assert not (tmp_path/'db').exists()


def test_remote_api_requires_token_and_cookie_is_usable(tmp_path):
    token='a-test-token-with-enough-length'
    server=create_server(tmp_path/'db',port=0,allow_remote=True,admin_token=token,
                         host_allowlist={'study.local'},allowed_origins={'http://study.local'})
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def request(path,method='GET',data=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
        try:
            conn.request(method,path,body=json.dumps(data) if data else None,
                         headers={'Host':'study.local',**(headers or {})})
            r=conn.getresponse();body=r.read();return r.status,dict(r.getheaders()),body
        finally:conn.close()
    try:
        assert request('/api/v1/papers')[0]==403
        assert request('/api/v1/papers',headers={'Authorization':'Bearer '+token})[0]==200
        assert request('/api/v1/papers',headers={'Authorization':'Bearer '+token,'Host':'other.local'})[0]==403
        assert request('/api/v1/auth','POST',{'token':token},headers={'Origin':'http://bad.local'})[0]==403
        status,headers,_=request('/api/v1/auth','POST',{'token':token},headers={'Origin':'http://study.local'})
        assert status==200 and 'HttpOnly' in headers['Set-Cookie']
        assert request('/api/v1/papers',headers={'Cookie':headers['Set-Cookie'].split(';')[0]})[0]==200
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();server.database.close()
