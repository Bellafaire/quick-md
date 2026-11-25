/*
 * Upload dropzones: big drag-and-drop targets that replace bare file
 * inputs while keeping the native file browser on click.
 *
 * Markup contract (per dropzone):
 *   <div class="upload-dropzone" data-for="the-file-input-id">…</div>
 *   <input type="file" id="the-file-input-id" style="display:none">
 *
 * Dropping a file assigns the drop event's FileList to the input (so the
 * form's `required` validation and existing submit/preview flow keep
 * working unchanged) and echoes the filename into the box. Clicking (or
 * Enter/Space) the box opens the input's native file browser.
 */
(function () {
    'use strict';

    function showDropzoneFilename(dropzone, file) {
        var nameSpan = dropzone.querySelector('.upload-dropzone-filename');
        if (!nameSpan) {
            nameSpan = document.createElement('span');
            nameSpan.className = 'upload-dropzone-filename';
            dropzone.appendChild(nameSpan);
        }
        nameSpan.textContent = file.name;
        nameSpan.title = file.name;
        dropzone.classList.add('has-file');
    }

    function resetUploadDropzone(dropzone) {
        dropzone.classList.remove('has-file', 'dragover');
        var nameSpan = dropzone.querySelector('.upload-dropzone-filename');
        if (nameSpan) nameSpan.remove();
    }

    function setupUploadDropzone(dropzone) {
        var inputId = dropzone.getAttribute('data-for');
        var input = document.getElementById(inputId);
        if (!dropzone || !input) return;

        // Click / keyboard activation -> native file browser (same dialog
        // the old bare input opened). preventDefault stops double-activation
        // via the wrapping <label>.
        dropzone.addEventListener('click', function (e) {
            e.preventDefault();
            input.click();
        });
        dropzone.setAttribute('tabindex', '0');
        dropzone.setAttribute('role', 'button');
        dropzone.setAttribute('aria-label', dropzone.getAttribute('aria-label') || 'Drop file here, or click to browse');
        dropzone.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                input.click();
            }
        });

        ['dragenter', 'dragover'].forEach(function (evt) {
            dropzone.addEventListener(evt, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });
        ['dragleave', 'drop'].forEach(function (evt) {
            dropzone.addEventListener(evt, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', function (e) {
            var files = e.dataTransfer && e.dataTransfer.files;
            if (files && files.length) {
                // Assign the drop event's FileList so the form field carries
                // the dropped file (also satisfies `required` validation).
                try { input.files = files; } catch (err) { /* no-op fallback */ }
                showDropzoneFilename(dropzone, files[0]);
                // Fire the input's change listeners (preview etc.) — they
                // were registered on the input after this installer ran.
                input.dispatchEvent(new Event('change'));
            }
        });

        // Keep the box in sync when a file is picked via the browser dialog.
        input.addEventListener('change', function () {
            if (input.files && input.files.length) {
                showDropzoneFilename(dropzone, input.files[0]);
            }
        });
    }

    // Install on every dropzone on the page; expose reset for pages that
    // need to clear the reflection (e.g. forms reset on dialog open).
    document.querySelectorAll('.upload-dropzone').forEach(setupUploadDropzone);
    window.qmdUploadDropzone = { reset: resetUploadDropzone };
})();
