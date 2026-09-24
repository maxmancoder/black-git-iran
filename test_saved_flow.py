# -*- coding: utf-8 -*-
"""Test Saved Messages -> send link -> click flow against a local mock."""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blackgit.transport.rubika.web import RubikaWebTransport

MOCK = """
<html><body>
<div class="chat-list">
  <div onclick="openSaved()">پیام‌های ذخیره شده</div>
</div>
<div id="chat" style="display:none">
  <div id="messages"></div>
  <textarea id="composer"></textarea>
  <button aria-label="send" onclick="sendMsg()">Send</button>
</div>
<script>
function openSaved(){document.getElementById('chat').style.display='block';}
function sendMsg(){
  var t=document.getElementById('composer').value;
  var d=document.createElement('div');
  var a=document.createElement('a');
  a.href=t; a.textContent=t;
  d.appendChild(a);
  document.getElementById('messages').appendChild(d);
  document.getElementById('composer').value='';
}
document.addEventListener('click', function(e){
  if(e.target && e.target.tagName==='A'){
    e.preventDefault();
    document.body.insertAdjacentHTML('beforeend','<div id="group">GROUP</div>');
  }
});
</script>
</body></html>
"""

URL = "https://rubika.ir/joing/BBGIIBIAC0YXLEQHIIXYJDWKHDCYRRDA"


def main() -> int:
    profile = Path(tempfile.mkdtemp(prefix="bgi-flow-"))
    t = RubikaWebTransport(profile, URL, headless=True)
    logs = []
    try:
        page = t._start(on_status=logs.append)
        page.set_content(MOCK)
        t._require_session(page)
        t._open_group(page, logs.append)
        n = page.locator("#group").count()
        assert n == 1, "did not enter group"
        print("FULL_OPEN_GROUP_OK")
        for line in logs:
            print("  -", line)
        return 0
    finally:
        t.close()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
