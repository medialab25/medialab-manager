// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(date) {
    return new Date(date).toLocaleString();
}

// File upload handling
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    fetch('/media/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log('File uploaded:', data);
            // Refresh media grid or show success message
        })
        .catch(error => {
            console.error('Upload error:', error);
            // Show error message
        });
}

// Media grid handling
function loadMediaGrid() {
    fetch('/media')
        .then(response => response.json())
        .then(data => {
            const mediaGrid = document.querySelector('.media-grid');
            if (!mediaGrid) return;

            mediaGrid.innerHTML = data.map(item => `
            <div class="media-item">
                <div class="media-preview">
                    <img src="/media/${item.filename}" alt="${item.filename}">
                </div>
                <div class="media-info">
                    <p>${item.filename}</p>
                    <p>${formatFileSize(item.size)}</p>
                    <p>${formatDate(item.uploaded_at)}</p>
                </div>
            </div>
        `).join('');
        })
        .catch(error => {
            console.error('Error loading media:', error);
        });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Load media grid if on dashboard or profile page
    if (document.querySelector('.media-grid')) {
        loadMediaGrid();
    }

    // Set up file upload handlers
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', handleFileUpload);
    });
}); 