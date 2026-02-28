/* ============================================
   Desert Shield Auto Paint — Notifications
   EmailJS Integration for Quote Form Submission
   ============================================ */

const Notifications = (() => {
  // EmailJS config — set via env vars or script config
  const SERVICE_ID = window.EMAILJS_SERVICE_ID || '';
  const TEMPLATE_ID = window.EMAILJS_TEMPLATE_ID || '';
  const PUBLIC_KEY = window.EMAILJS_PUBLIC_KEY || '';

  let initialized = false;

  function init() {
    if (typeof emailjs !== 'undefined' && PUBLIC_KEY) {
      emailjs.init(PUBLIC_KEY);
      initialized = true;
      console.log('EmailJS initialized');
    } else {
      console.log('EmailJS not configured — form submissions will be logged to console');
    }
  }

  async function send(formData) {
    console.log('Quote Request Submitted:', formData);

    // If EmailJS is configured, send the email
    if (initialized && SERVICE_ID && TEMPLATE_ID) {
      try {
        // Build image summary for email
        const imageInfo = formData.images && formData.images.length > 0
          ? `${formData.images.length} photo(s) attached`
          : 'No photos uploaded';

        const templateParams = {
          customer_name: formData.name,
          customer_phone: formData.phone,
          customer_email: formData.email || 'Not provided',
          vehicle_info: formData.vehicle,
          vehicle_color: formData.color || 'Not specified',
          service_type: formData.serviceType,
          damage_description: formData.description || 'No description provided',
          image_count: imageInfo,
          submission_time: new Date().toLocaleString('en-US', {
            timeZone: 'America/Los_Angeles',
            dateStyle: 'medium',
            timeStyle: 'short'
          }),
        };

        // Attach first image as base64 if available (EmailJS supports limited attachments)
        if (formData.images && formData.images.length > 0) {
          templateParams.image_1 = formData.images[0].base64;
        }

        const result = await emailjs.send(SERVICE_ID, TEMPLATE_ID, templateParams);
        console.log('Email notification sent:', result);
        return result;
      } catch (err) {
        console.error('EmailJS error:', err);
        // Fall through to backup logging
      }
    }

    // Backup: Log to console and save to localStorage
    saveLocally(formData);
    return { status: 200, text: 'Saved locally' };
  }

  function saveLocally(formData) {
    try {
      const submissions = JSON.parse(localStorage.getItem('ds_submissions') || '[]');
      submissions.push({
        ...formData,
        images: formData.images ? formData.images.map(i => ({ name: i.name, type: i.type })) : [],
        savedAt: new Date().toISOString(),
      });
      localStorage.setItem('ds_submissions', JSON.stringify(submissions));
      console.log('Quote saved to localStorage as backup');
    } catch (e) {
      console.error('Failed to save locally:', e);
    }
  }

  // Initialize on load
  document.addEventListener('DOMContentLoaded', init);

  return { send, init };
})();
