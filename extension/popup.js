document.addEventListener('DOMContentLoaded', async () => {
  const folders = await getBookmarkFolders();
  await renderFolders(folders);
});

async function getBookmarkFolders() {
  const tree = await chrome.bookmarks.getTree();
  const folders = [];

  function traverse(node) {
    if (node.children) {
      if (node.id !== '0') folders.push(node); // exclude root
      node.children.forEach(traverse);
    }
  }

  traverse(tree[0]);
  return folders;
}

async function renderFolders(folders) {
  const container = document.getElementById('foldersList');
  container.innerHTML = '';

  const storedStates = await chrome.storage.local.get('folderStates');
  const folderStates = storedStates.folderStates || {};

  folders.forEach(folder => {
    const item = document.createElement('div');
    item.className = 'folder-item';

    const toggle = document.createElement('div');
    toggle.className = 'toggle';
    toggle.dataset.folderId = folder.id;
    const initialState = folderStates[folder.id]?.state || 0;
    updateToggleState(toggle, initialState);

    toggle.addEventListener('click', async () => {
      const currentState = parseInt(toggle.dataset.state);
      const newState = (currentState + 1) % 3;
      await saveToggleState(folder.id, newState);
      updateToggleState(toggle, newState);
    });

    const title = document.createElement('span');
    title.textContent = folder.title;

    const planetBtn = document.createElement('button');
    planetBtn.innerHTML = '🌐';
    planetBtn.className = 'planet-btn';
    planetBtn.addEventListener('click', () => handleShare(folder, initialState === 2));

    item.append(toggle, title, planetBtn);
    container.appendChild(item);
  });
}

async function saveToggleState(folderId, state) {
  const storedStates = await chrome.storage.local.get('folderStates');
  const folderStates = storedStates.folderStates || {};
  folderStates[folderId] = { state };
  await chrome.storage.local.set({ folderStates });
}

function updateToggleState(element, state) {
  const icons = ['❌', '📗', '👑'];
  element.textContent = icons[state];
  element.dataset.state = state;
}

async function handleShare(folder, canWrite) {
  try {
    const bookmarks = await getBookmarksRecursive(folder);
    const response = await fetch('http://localhost:8000/api/share', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_id: folder.id,
        name: folder.title,
        bookmarks: bookmarks,
        can_write: canWrite,
        sharemark_uuid: await chrome.storage.local.get('sharemark_uuid')
      })
    });

    const data = await response.json();
    showShareUrl(data.share_url);

    chrome.runtime.sendMessage({ type: 'initWebSocket', shareId: data.share_id });

  } catch (error) {
    console.error('Ошибка:', error.message);
  }
}

async function getBookmarksRecursive(node) {
  const bookmarks = [];

  async function traverse(node) {
    if (node.url) {
      bookmarks.push({ title: node.title, url: node.url });
    }
    if (node.children) {
      for (const child of node.children) {
        await traverse(child);
      }
    }
  }

  await traverse(node);
  return bookmarks;
}

function showShareUrl(url) {
  const modal = document.createElement('div');
  modal.innerHTML = `
    <div class="share-modal">
      <p>Ссылка для доступа:</p>
      <input type="text" value="${url}" readonly>
      <button onclick="navigator.clipboard.writeText('${url}')">Копировать</button>
    </div>
  `;
  document.body.appendChild(modal);
}
