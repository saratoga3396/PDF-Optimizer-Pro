document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const statusContainer = document.getElementById('status-container');
    const resultContainer = document.getElementById('result-container');
    const dropZoneContent = dropZone.innerHTML;

    // Events for Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Click to select
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Reset Button
    document.getElementById('reset-btn').addEventListener('click', () => {
        resultContainer.classList.add('hidden');
        dropZone.classList.remove('hidden');
        dropZone.innerHTML = dropZoneContent; // Restore icon
        statusContainer.classList.add('hidden');
        fileInput.value = '';
    });

    function handleFile(file) {
        if (file.type !== 'application/pdf') {
            alert('PDFファイルのみ対応しています。');
            return;
        }

        // Show loading state
        dropZone.classList.add('hidden');
        statusContainer.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', file);

        // Add options
        const makeSearchable = document.getElementById('make-searchable').checked;
        const enhanceImage = document.getElementById('enhance-image').checked;

        formData.append('searchable', makeSearchable);
        formData.append('enhance', enhanceImage);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                statusContainer.classList.add('hidden');

                if (data.error) {
                    alert('エラー: ' + data.error);
                    dropZone.classList.remove('hidden');
                } else {
                    // Show result
                    resultContainer.classList.remove('hidden');
                    document.getElementById('new-filename').textContent = data.filename;
                    document.getElementById('download-btn').href = data.download_url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusContainer.classList.add('hidden');
                dropZone.classList.remove('hidden');
                alert('アップロードに失敗しました。');
            });
    }
});
