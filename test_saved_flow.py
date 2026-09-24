# -*- coding: utf-8 -*-
"""Test Saved Messages -> send link -> click flow against a local mock.

Mock mirrors real Rubika Web (Angular) DOM classes:
  [rb-chat-item] .peer-title | textarea.input-message-input | .btn-send
  [rb-message-text] a[href*=joing]
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blackgit.transport.rubika.web import RubikaWebTransport

MOCK = """
<html><body>
<div class="chatlist-container">
  <div rb-chat-item class="chatlist-chat" onclick="openSaved()">
    <span class="peer-title">پیام های ذخیره شده</span>
  </div>
  <div rb-chat-item class="chatlist-chat">
    <span class="peer-title">Some Other Chat</span>
  </div>
</div>
<div id="chat" style="display:none">
  <div id="messages"></div>
  <textarea class="input-message-input" name="draftMessage" id="composer"></textarea>
  <button class="btn-send" onclick="sendMsg()">Send</button>
</div>
<script>
function openSaved(){document.getElementById('chat').style.display='block';}
function sendMsg(){
  var t=document.getElementById('composer').value;
  var d=document.createElement('div');
  d.setAttribute('rb-message-text','');
  var a=document.createElement('a');
  a.href=t; a.textContent=t;
  d.appendChild(a);
  document.getElementById('messages').appendChild(d);
  document.getElementById('composer').value='';
}
document.addEventListener('click', function(e){
  var a = e.target && e.target.closest ? e.target.closest('a') : null;
  if(a){
    e.preventDefault();
    if(!document.getElementById('group'))
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
