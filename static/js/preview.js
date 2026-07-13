function openPreview(fileId, fileType, filename) {
    const overlay = document.getElementById('preview-overlay');
    const content = document.getElementById('preview-content');
    const title = document.getElementById('preview-title');

    if (!overlay || !content) {
        // 动态创建预览弹窗
        createPreviewModal();
        return openPreview(fileId, fileType, filename);
    }

    const url = '/file/' + fileId + '/serve';
    title.textContent = filename;

    if (fileType === 'image') {
        content.innerHTML = '<img src="' + url + '" alt="' + filename + '" class="preview-media">';
    } else {
        content.innerHTML = '<video src="' + url + '" controls preload="metadata" class="preview-media"></video>';
    }

    overlay.classList.add('active');
}

function createPreviewModal() {
    const overlay = document.createElement('div');
    overlay.id = 'preview-overlay';
    overlay.className = 'preview-overlay';
    overlay.innerHTML = `
        <div class="preview-box">
            <div class="preview-header">
                <span id="preview-title"></span>
                <button class="preview-close" onclick="closePreview()">&times;</button>
            </div>
            <div id="preview-content" class="preview-body"></div>
        </div>
    `;
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closePreview();
    });
    document.body.appendChild(overlay);
}

function closePreview() {
    const overlay = document.getElementById('preview-overlay');
    if (overlay) {
        overlay.classList.remove('active');
        document.getElementById('preview-content').innerHTML = '';
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closePreview();
});
