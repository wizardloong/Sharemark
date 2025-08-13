async function init() {
    const params = new URLSearchParams(window.location.search);
    const shareId = params.get("share_id");

    if (!shareId) {
        document.body.innerHTML = "<h3>Ошибка: share_id не передан</h3>";
        return;
    }

    try {
        // Достаём UUID владельца из локального хранилища расширения
        const { sharemark_uuid } = await chrome.storage.local.get("sharemark_uuid");

        if (!sharemark_uuid) {
            document.body.innerHTML = "<h3>Ошибка: не найден sharemark_uuid</h3>";
            return;
        }

        // Делаем запрос на бэкенд
        const response = await fetch(`http://localhost:8000/share?share_id=${shareId}&sharemark_uuid=${sharemark_uuid}`);
        const data = await response.json();

        if (response.ok) {
            document.body.innerHTML = "<h3>Данные отправлены по WebSocket!</h3>";
        } else {
            document.body.innerHTML = `<h3>Ошибка: ${data.detail || "Неизвестная ошибка"}</h3>`;
        }

    } catch (err) {
        document.body.innerHTML = `<h3>Ошибка запроса: ${err.message}</h3>`;
    }
}

init();