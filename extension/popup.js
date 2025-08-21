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

    // Достаём UUID владельца
    const { sharemark_uuid } = await chrome.storage.local.get('sharemark_uuid');
    if (!sharemark_uuid) {
      alert("Ошибка: не найден sharemark_uuid. Проверьте настройки расширения.");
      return;
    }

    // Отправляем на бэкенд
    const response = await fetch('https://getsharemark.com/api/share', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_id: folder.id,
        name: folder.title,
        bookmarks: bookmarks,
        can_write: canWrite,
        sharemark_uuid
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Ошибка при создании расшаривания');
    }

    // Формируем ссылку на фронтенд-страницу open-share
    // const shareUrl = `chrome-extension://${chrome.runtime.id}/open_share.html?share_id=${data.share_id}`;
    const shareUrl = data.share_url;

    // Копируем в буфер обмена
    await navigator.clipboard.writeText(shareUrl);
    alert("Ссылка скопирована в буфер обмена:\n" + shareUrl);

    // Инициируем вебсокет соединение у владельца
    chrome.runtime.sendMessage({ type: 'initWebSocket', shareId: data.share_id });

  } catch (error) {
    console.error('Ошибка:', error.message);
    alert("Ошибка: " + error.message);
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
