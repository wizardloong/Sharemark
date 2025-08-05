const params = new URLSearchParams(window.location.search);
const folderId = params.get('folderId');

document.getElementById('shareBtn').addEventListener('click', async () => {
  const email = document.getElementById('email').value;

  try {
    const response = await fetch('https://your-api-domain.com/share', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        folderId,
        email,
        timestamp: new Date().toISOString()
      })
    });

    if (response.ok) {
      alert('Приглашение успешно отправлено!');
      window.close();
    } else {
      throw new Error('Ошибка сервера');
    }
  } catch (error) {
    alert('Ошибка: ' + error.message);
  }
});
