require('dotenv').config();

document.addEventListener('DOMContentLoaded', async () => {  
  const writeCheckbox = document.getElementById('write-access');
  const shareLinkInput = document.getElementById('share-link');
  const copyBtn = document.getElementById('copy-link');

  const { folderIdToShare } = await chrome.storage.local.get('folderIdToShare');

  let writeAccess = false;

  function generateShareLink(folderId, write) {
    const token = crypto.randomUUID(); // временный токен
    return `${process.env.DOMAIN_NAME}/share/${folderId}?token=${token}&write=${write ? 1 : 0}`;
  }

  function updateLink() {
    const link = generateShareLink(folderIdToShare, writeAccess);
    shareLinkInput.value = link;
  }

  writeCheckbox.addEventListener('change', () => {
    writeAccess = writeCheckbox.checked;
    updateLink();
  });

  copyBtn.addEventListener('click', () => {
    shareLinkInput.select();
    document.execCommand('copy');
  });

  updateLink();
});
