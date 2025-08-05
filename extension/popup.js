function renderBookmarks(bookmarks, container) {
  bookmarks.forEach(node => {
    if (node.url) return;

    const div = document.createElement('div');
    div.className = 'folder';
    div.textContent = '📁 ' + node.title;
    div.onclick = () => shareFolder(node.id);

    if (node.children) {
      const childContainer = document.createElement('div');
      childContainer.style.marginLeft = '15px';
      renderBookmarks(node.children, childContainer);
      div.appendChild(childContainer);
    }

    container.appendChild(div);
  });
}

function shareFolder(folderId) {
  chrome.windows.create({
    url: chrome.runtime.getURL(`share_modal.html?folderId=${folderId}`),
    type: 'popup',
    width: 400,
    height: 300
  });
}

chrome.bookmarks.getTree(tree => {
  const container = document.getElementById('folderTree');
  renderBookmarks(tree[0].children, container);
});
