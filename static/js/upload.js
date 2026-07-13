function initUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const progressBar = document.getElementById('progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    if (!dropZone || !fileInput) return;

    // 点击触发文件选择
    dropZone.addEventListener('click', () => fileInput.click());

    // 文件选择后上传
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
        }
    });

    // 拖拽事件
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });
}

function uploadFile(file) {
    const progressBar = document.getElementById('progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const dropText = document.getElementById('drop-text');

    // 检查文件大小 (100MB)
    if (file.size > 100 * 1024 * 1024) {
        alert('文件大小不能超过100MB');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressFill.style.width = percent + '%';
            progressText.textContent = percent + '%';
        }
    });

    xhr.addEventListener('load', () => {
        try {
            const resp = JSON.parse(xhr.responseText);
            if (resp.success) {
                progressText.textContent = '上传成功！';
                dropText.textContent = resp.message || '上传成功，点击继续上传';
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                progressText.textContent = '上传失败';
                dropText.textContent = resp.error || '上传失败，请重试';
            }
        } catch (e) {
            progressText.textContent = '上传失败';
            dropText.textContent = '服务器错误，请重试';
        }
    });

    xhr.addEventListener('error', () => {
        progressText.textContent = '网络错误';
        dropText.textContent = '上传失败，请检查网络后重试';
    });

    xhr.open('POST', '/upload');
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    dropText.textContent = '正在上传...';
    xhr.send(formData);
}

function deleteFile(fileId) {
    if (!confirm('确定要删除这个文件吗？')) return;

    fetch('/file/' + fileId, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const card = document.getElementById('file-card-' + fileId);
                if (card) card.remove();
            } else {
                alert(data.error || '删除失败');
            }
        });
}

document.addEventListener('DOMContentLoaded', initUpload);
