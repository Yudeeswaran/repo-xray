import subprocess
from skills.xray.git import is_repo, head, log, search_history

def git(cwd,*args):
    subprocess.run(["git",*args],cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

def test_git_history_adapter(tmp_path):
    git(tmp_path,"init","-q")
    git(tmp_path,"config","user.email","x@example.com")
    git(tmp_path,"config","user.name","x")
    f=tmp_path/"config.py"; f.write_text("TIMEOUT = 60\n")
    git(tmp_path,"add","."); git(tmp_path,"commit","-qm","set timeout")
    assert is_repo(tmp_path)
    assert head(tmp_path)
    assert log(tmp_path,5)[0]["message"]=="set timeout"
    assert search_history(tmp_path,"TIMEOUT",5)
