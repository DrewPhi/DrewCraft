import base64
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from publish_dh_preload import verify


def test_publication_signature_rejects_modified_catalog(tmp_path):
    private=tmp_path/'key.pem'
    public=tmp_path/'public.pem'
    subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(private)],check=True,capture_output=True)
    subprocess.run(['openssl','pkey','-in',str(private),'-pubout','-out',str(public)],check=True,capture_output=True)
    source=tmp_path/'source.json'
    source.write_bytes(b'{"valid":true}')
    signature=subprocess.check_output(['openssl','dgst','-sha256','-sign',str(private),str(source)])
    envelope={'catalog':base64.b64encode(source.read_bytes()).decode(), 'signature':base64.b64encode(signature).decode()}
    assert verify(envelope,public,tmp_path)=={'valid':True}
    envelope['catalog']=base64.b64encode(b'{"valid":false}').decode()
    with pytest.raises(subprocess.CalledProcessError):
        verify(envelope,public,tmp_path)


@pytest.mark.parametrize('name',['../health.json','%2e%2e/health.json','catalog.json','key.pem','a'*64+'.sqlite?x=1'])
def test_public_lod_route_is_not_a_file_browser(tmp_path,name):
    spec=importlib.util.spec_from_file_location('lod_health', ROOT/'infra/health_server.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors=[]
    handler=SimpleNamespace(path='/lod-export/'+name,lod_root=tmp_path,send_error=errors.append)
    module.Handler.lod_file(handler)
    assert errors==[404]


def test_public_lod_route_rejects_symlink_outside_root(tmp_path):
    spec=importlib.util.spec_from_file_location('lod_health', ROOT/'infra/health_server.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory=tmp_path/'public'
    directory.mkdir()
    private=tmp_path/'private.sqlite'
    private.write_bytes(b'PRIVATE')
    (directory/('a'*64+'.sqlite')).symlink_to(private)
    errors=[]
    module.Handler.lod_file(SimpleNamespace(path='/lod-export/'+'a'*64+'.sqlite',lod_root=directory,send_error=errors.append))
    assert errors==[404]
