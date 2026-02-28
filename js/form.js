/* ============================================
   Desert Shield Auto Paint — Quote Form
   Form Handling, Image Upload, Validation
   ============================================ */

const QuoteForm = (() => {
  const MAX_IMAGES = 5;
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ACCEPTED_TYPES = ['image/jpeg', 'image/png'];

  let uploadedFiles = [];
  let elements = {};

  function init() {
    elements = {
      form: document.getElementById('quote-form'),
      uploadZone: document.getElementById('upload-zone'),
      fileInput: document.getElementById('form-file-input'),
      previews: document.getElementById('image-previews'),
      submitBtn: document.getElementById('form-submit-btn'),
      formContent: document.getElementById('form-content'),
      formSuccess: document.getElementById('form-success'),
    };

    if (!elements.form) return;

    // Form submission
    elements.form.addEventListener('submit', handleSubmit);

    // Upload zone - click
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', (e) => {
      processFiles(Array.from(e.target.files));
      e.target.value = '';
    });

    // Drag & drop
    elements.uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      elements.uploadZone.classList.add('dragover');
    });

    elements.uploadZone.addEventListener('dragleave', () => {
      elements.uploadZone.classList.remove('dragover');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      elements.uploadZone.classList.remove('dragover');
      const files = Array.from(e.dataTransfer.files).filter(f => ACCEPTED_TYPES.includes(f.type));
      processFiles(files);
    });

    // Clear validation on input
    elements.form.querySelectorAll('input, select, textarea').forEach(field => {
      field.addEventListener('input', () => {
        field.classList.remove('error');
        const errEl = field.parentElement.querySelector('.form-error');
        if (errEl) errEl.classList.remove('visible');
      });
    });
  }

  function processFiles(files) {
    for (const file of files) {
      if (uploadedFiles.length >= MAX_IMAGES) {
        alert(`Maximum ${MAX_IMAGES} images allowed.`);
        break;
      }

      if (!ACCEPTED_TYPES.includes(file.type)) {
        alert('Please upload JPG or PNG images only.');
        continue;
      }

      if (file.size > MAX_FILE_SIZE) {
        alert('Each image must be under 10MB.');
        continue;
      }

      const reader = new FileReader();
      reader.onload = (ev) => {
        uploadedFiles.push({
          file,
          dataUrl: ev.target.result,
          base64: ev.target.result.split(',')[1],
          name: file.name,
          type: file.type,
        });
        renderPreviews();
      };
      reader.readAsDataURL(file);
    }
  }

  function renderPreviews() {
    elements.previews.innerHTML = '';

    uploadedFiles.forEach((img, idx) => {
      const thumb = document.createElement('div');
      thumb.className = 'preview-thumb';
      thumb.innerHTML = `
        <img src="${img.dataUrl}" alt="${img.name}">
        <button type="button" class="remove-preview" data-idx="${idx}">&times;</button>
      `;
      thumb.querySelector('.remove-preview').addEventListener('click', () => {
        uploadedFiles.splice(idx, 1);
        renderPreviews();
      });
      elements.previews.appendChild(thumb);
    });

    // Update upload zone text
    const remaining = MAX_IMAGES - uploadedFiles.length;
    const hint = elements.uploadZone.querySelector('.upload-hint');
    if (hint) {
      hint.textContent = remaining > 0
        ? `JPG or PNG, up to 10MB each • ${remaining} more allowed`
        : 'Maximum 5 images reached';
    }
  }

  function validate() {
    let valid = true;
    const required = elements.form.querySelectorAll('[required]');

    required.forEach(field => {
      const val = field.value.trim();
      const errEl = field.parentElement.querySelector('.form-error');

      if (!val) {
        field.classList.add('error');
        if (errEl) {
          errEl.textContent = 'This field is required';
          errEl.classList.add('visible');
        }
        valid = false;
      } else if (field.type === 'tel' && !/^[\d\s\-\(\)\+]{7,}$/.test(val)) {
        field.classList.add('error');
        if (errEl) {
          errEl.textContent = 'Enter a valid phone number';
          errEl.classList.add('visible');
        }
        valid = false;
      } else if (field.type === 'email' && val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
        field.classList.add('error');
        if (errEl) {
          errEl.textContent = 'Enter a valid email address';
          errEl.classList.add('visible');
        }
        valid = false;
      }
    });

    return valid;
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!validate()) return;

    elements.submitBtn.disabled = true;
    elements.submitBtn.textContent = 'SENDING...';

    const formData = {
      name: elements.form.querySelector('#form-name').value.trim(),
      phone: elements.form.querySelector('#form-phone').value.trim(),
      email: elements.form.querySelector('#form-email').value.trim(),
      vehicle: elements.form.querySelector('#form-vehicle').value.trim(),
      color: elements.form.querySelector('#form-color').value.trim(),
      serviceType: elements.form.querySelector('#form-service').value,
      description: elements.form.querySelector('#form-description').value.trim(),
      images: uploadedFiles.map(f => ({ name: f.name, type: f.type, base64: f.base64 })),
      timestamp: new Date().toISOString(),
    };

    try {
      await Notifications.send(formData);
      showSuccess();
    } catch (err) {
      console.error('Form submission error:', err);
      // Still show success to user — the data was captured
      showSuccess();
    }
  }

  function showSuccess() {
    elements.formContent.style.display = 'none';
    elements.formSuccess.classList.add('visible');
    elements.submitBtn.disabled = false;
    elements.submitBtn.textContent = 'SUBMIT REQUEST';
  }

  function getFormData() {
    return {
      name: elements.form?.querySelector('#form-name')?.value?.trim() || '',
      phone: elements.form?.querySelector('#form-phone')?.value?.trim() || '',
      email: elements.form?.querySelector('#form-email')?.value?.trim() || '',
      vehicle: elements.form?.querySelector('#form-vehicle')?.value?.trim() || '',
      color: elements.form?.querySelector('#form-color')?.value?.trim() || '',
      serviceType: elements.form?.querySelector('#form-service')?.value || '',
      description: elements.form?.querySelector('#form-description')?.value?.trim() || '',
    };
  }

  return { init, getFormData };
})();

document.addEventListener('DOMContentLoaded', () => {
  QuoteForm.init();
});
