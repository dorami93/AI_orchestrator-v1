const $ = (id) => document.getElementById(id);
const sidebar = $('sidebar'), chatList = $('chatList'), messagesEl = $('messages');
const inputForm = $('inputForm'), input = $('input'), sendBtn = $('sendBtn'), chatTitle = $('chatTitle');
const settingsModal = $('settingsModal'), apiKeyInput = $('apiKeyInput'), modelInput = $('modelInput');

let chats = JSON.parse(localStorage.getItem('chats') || '[]');
let currentId = localStorage.getItem('currentId');
let sending = false;

function saveChats() { localStorage.setItem('chats', JSON.stringify(chats)); }
function getCurrent() { return chats.find(c => c.id === currentId); }

function newChat() {
  const chat = { id: Date.now().toString(), title: '新規チャット', messages: [] };
  chats.unshift(chat);
  currentId = chat.id;
  localStorage.setItem('currentId', currentId);
  saveChats();
  renderChatList();
  renderMessages();
  sidebar.classList.remove('show');
}

function deleteChat(id, e) {
  e.stopPropagation();
  if (!confirm('このチャットを削除しますか？')) return;
  chats = chats.filter(c => c.id !== id);
  if (currentId === id) currentId = chats[0]?.id || null;
  saveChats();
  localStorage.setItem('currentId', currentId || '');
  renderChatList();
  renderMessages();
}

function renderChatList() {
  chatList.innerHTML = '';
  chats.forEach(c => {
    const div = document.createElement('div');
    div.className = 'chatItem' + (c.id === currentId ? ' active' : '');
    div.innerHTML = `<span></span><button>×</button>`;
    div.querySelector('span').textContent = c.title;
    div.onclick = () => { currentId = c.id; localStorage.setItem('currentId', currentId); renderChatList(); renderMessages(); sidebar.classList.remove('show'); };
    div.querySelector('button').onclick = (e) => deleteChat(c.id, e);
    chatList.appendChild(div);
  });
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (m, lang, code) =>
    `<pre><code>${code}</code><button class="copyBtn" onclick="copyCode(this)">コピー</button></pre>`);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  return html;
}

function copyCode(btn) {
  const code = btn.previousElementSibling.textContent;
  navigator.clipboard.writeText(code);
  btn.textContent = 'コピー済';
  setTimeout(() => btn.textContent = 'コピー', 1500);
}

function renderMessages() {
  const chat = getCurrent();
  messagesEl.innerHTML = '';
  chatTitle.textContent = chat ? chat.title : 'Groq Chat';
  if (!chat) return;
  chat.messages.forEach(m => {
    const div = document.createElement('div');
    div.className = 'msg ' + m.role;
    div.innerHTML = renderMarkdown(m.content);
    messagesEl.appendChild(div);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function autoResize() {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 150) + 'px';
}
input.addEventListener('input', autoResize);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inputForm.requestSubmit(); }
});

$('newChatBtn').onclick = newChat;
$('menuBtn').onclick = () => sidebar.classList.toggle('show');
$('settingsBtn').onclick = openSettings;
$('closeSettingsBtn').onclick = () => settingsModal.classList.add('hidden');
$('saveSettingsBtn').onclick = () => {
  localStorage.setItem('apiKey', apiKeyInput.value.trim());
  localStorage.setItem('model', modelInput.value.trim() || 'llama-3.3-70b-versatile');
  settingsModal.classList.add('hidden');
};

function openSettings() {
  apiKeyInput.value = localStorage.getItem('apiKey') || '';
  modelInput.value = localStorage.getItem('model') || 'llama-3.3-70b-versatile';
  settingsModal.classList.remove('hidden');
}

inputForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (sending) return;
  const text = input.value.trim();
  if (!text) return;
  const apiKey = localStorage.getItem('apiKey');
  if (!apiKey) { openSettings(); return; }

  if (!getCurrent()) newChat();
  const chat = getCurrent();
  chat.messages.push({ role: 'user', content: text });
  if (chat.title === '新規チャット') chat.title = text.slice(0, 20);
  input.value = '';
  autoResize();
  renderChatList();
  renderMessages();
  saveChats();

  sending = true;
  sendBtn.disabled = true;
  const assistantMsg = { role: 'assistant', content: '' };
  chat.messages.push(assistantMsg);

  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
      body: JSON.stringify({
        model: localStorage.getItem('model') || 'llama-3.3-70b-versatile',
        messages: chat.messages.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
        stream: true
      })
    });
    if (!res.ok) throw new Error('API error: ' + res.status);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') continue;
        try {
          const json = JSON.parse(data);
          const delta = json.choices[0].delta.content;
          if (delta) { assistantMsg.content += delta; renderMessages(); }
        } catch {}
      }
    }
  } catch (err) {
    assistantMsg.content = 'エラー: ' + err.message;
    renderMessages();
  }

  sending = false;
  sendBtn.disabled = false;
  saveChats();
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}

renderChatList();
renderMessages();
