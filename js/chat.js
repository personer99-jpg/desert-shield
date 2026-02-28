/* ============================================
   Desert Shield Auto Paint — AI Chat Assistant
   Smart Keyword Chatbot (No API Key Required)
   Upgrade path: Add Gemini API key for full AI
   ============================================ */

const ChatAssistant = (() => {
  const MAX_IMAGES = 5;
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  const ACCEPTED_TYPES = ['image/jpeg', 'image/png'];

  // ---- Knowledge Base ----
  const responses = {
    greeting: {
      patterns: /^(hi|hey|hello|howdy|sup|what'?s up|good (morning|afternoon|evening)|yo)\b/i,
      reply: `Hey there! 👋 Welcome to Desert Shield Auto Paint. I can help you with:\n\n• **Our services** — mobile & shop repairs\n• **Pricing estimates** — what repairs typically cost\n• **Mobile vs. shop** — which option fits your situation\n• **Why skip insurance** — save money & hassle\n• **Service area** — cities we cover\n\nWhat can I help you with?`
    },

    services: {
      patterns: /\b(service|what (do|can) you|offer|types?|do you do|what you do|help me with)\b/i,
      reply: `We offer two main types of service:\n\n🚗 **Mobile Service (We Come To You)**\nFor minor repairs — scratches, scuffs, bumper blending, small dents, and paint touch-ups. We come to your home, office, or dealership lot.\n\n🔧 **Shop Drop-Off**\nFor major work — collision damage, full panel repaints, complete color changes, and extensive body repair. Drop your vehicle at our shop.\n\n🏢 **Dealership Services**\nWe partner with dealerships across the High Desert for lot-ready paint repair and reconditioning.\n\nWhat type of repair are you looking for?`
    },

    pricing: {
      patterns: /\b(pric|cost|how much|expens|cheap|afford|rate|estimat|quote|ballpark|range)\b/i,
      reply: `Here are some rough pricing ranges to give you an idea:\n\n• **Scratch/scuff repair:** $150–$400\n• **Bumper blend/respray:** $300–$600\n• **Small dent + paint:** $250–$500\n• **Full panel repaint:** $500–$1,200\n• **Major collision repair:** Varies — send photos!\n• **Complete color change:** $3,000–$7,000+\n\nThese are estimates — exact pricing depends on the specific damage. Upload some photos in our **quote form** below or send them here, and Ryan will give you an accurate price!`
    },

    mobile: {
      patterns: /\b(come to|mobile|my (location|house|home|place|work|office)|on.?site|travel to|drive to|where (are|do) you|you come)\b/i,
      reply: `Yes! For **minor repairs**, we come directly to you — anywhere in the High Desert. 🚗\n\nThis includes:\n• Your home or apartment\n• Your workplace or office\n• Dealership lots\n\n**Mobile-friendly repairs:** scratches, scuffs, small dents, bumper touch-ups, paint blending.\n\nFor **major work** like collision damage, full repaints, or color changes, those are done at our shop where we have the full equipment setup.\n\nWhere are you located? I can confirm we service your area!`
    },

    insurance: {
      patterns: /\b(insurance|deductib|claim|skip|instead of|better than|why not|save money|premium|rate (hike|increase))\b/i,
      reply: `Great question — skipping insurance is often the **smarter move**. Here's why:\n\n✅ Our repairs are often **cheaper than your deductible** ($500–$1,000+)\n✅ **No rate increases** — a claim can raise your premiums for years\n✅ **No paperwork** — skip the claims process entirely\n✅ **Faster turnaround** — days, not weeks\n✅ **No rental car hassle** — mobile repairs happen at your location\n✅ **Clean record** — no claim on your insurance history\n\nFor most cosmetic and minor collision damage, you'll come out ahead paying out of pocket with us. Want a free estimate to compare?`
    },

    area: {
      patterns: /\b(area|where|location|city|cities|cover|victorville|hesperia|apple valley|adelanto|barstow|phelan|oak hills|lucerne|wrightwood|pinon|oro grande|spring valley)\b/i,
      reply: `We serve the **entire High Desert region** of Southern California! 📍\n\nOur service area includes:\nVictorville, Hesperia, Apple Valley, Adelanto, Lucerne Valley, Phelan, Oak Hills, Spring Valley Lake, Barstow, Oro Grande, Pinon Hills, Wrightwood, and surrounding communities.\n\nOur **mobile service** comes directly to your location. For **shop work**, our shop is in the Victorville area.\n\nAre you in one of these areas?`
    },

    hours: {
      patterns: /\b(hour|open|close|when|schedule|time|availab|weekend|saturday|sunday)\b/i,
      reply: `Our hours are:\n\n🕗 **Monday – Saturday:** 8:00 AM – 6:00 PM\n🚫 **Sunday:** Closed\n\nWant to set up an appointment? You can submit a **free quote request** below, or call us at **(760) 555-0199**!`
    },

    scratch: {
      patterns: /\b(scratch|scratched|key|keyed|scuff|scrape|scraped|mark|swirl)\b/i,
      reply: `Scratches and scuffs are one of our most common repairs — and the good news is, this is typically a **mobile service** job. We can come to you! 🚗\n\nDepending on the depth and size:\n• **Light scratches/scuffs:** $150–$300\n• **Deeper scratches/keying:** $250–$400+\n\nThe best way to get an accurate price is to **upload a photo** of the damage. You can share it right here in this chat or use the quote form below!`
    },

    bumper: {
      patterns: /\b(bumper|fender|front end|rear end|fender bender)\b/i,
      reply: `Bumper repairs are another one of our specialties! Depending on the damage:\n\n🚗 **Minor bumper scuffs/scratches** — Mobile service, $200–$400\n🚗 **Bumper respray/blend** — Mobile service, $300–$600\n🔧 **Cracked/heavily damaged bumper** — May need shop work\n\nSend us a photo of the damage and we'll let you know if it's a mobile fix or shop job, plus give you an accurate estimate!`
    },

    dent: {
      patterns: /\b(dent|ding|door ding|hail|dimple|crease)\b/i,
      reply: `Dents and dings are very fixable! Here's the general breakdown:\n\n🚗 **Small dents/door dings** — Often mobile-friendly, $250–$500\n🔧 **Large dents/creases** — May need shop work depending on severity\n🔧 **Hail damage** — Usually a shop job for multiple dents\n\nThe key factor is whether the paint is cracked or just dented. **Upload a photo** and we can tell you exactly what's needed!`
    },

    collision: {
      patterns: /\b(collision|crash|accident|wreck|hit|totaled|smash|crumple|body damage|major damage|big damage)\b/i,
      reply: `For collision and major body damage, that would be a **shop drop-off** job. 🔧\n\nWe handle:\n• Full collision repair and restoration\n• Panel replacement and repainting\n• Frame-level body work\n• Complete refinishing\n\nPricing varies based on the extent of the damage — the best next step is to **send us photos** or bring the vehicle by for an assessment.\n\nAnd remember — for many repairs, going through us directly is **cheaper than your insurance deductible** with none of the hassle!`
    },

    color_change: {
      patterns: /\b(color change|full paint|whole car|repaint|new color|wrap|respray entire|paint (the )?whole)\b/i,
      reply: `Complete color changes and full vehicle repaints are done at our **shop**. 🔧\n\n• **Full color change:** $3,000–$7,000+ depending on the vehicle size and color\n• **Same-color full respray:** Can be less depending on condition\n\nThis includes full prep, primer, basecoat, clearcoat, and finishing. Ryan has 15+ years of experience delivering factory-quality results.\n\nWant to discuss options? Call us at **(760) 555-0199** or submit a quote request below!`
    },

    dealership: {
      patterns: /\b(dealer|dealership|lot|inventory|recon|wholesale)\b/i,
      reply: `We love working with dealerships! 🏢\n\nOur dealership services include:\n• **On-site mobile repairs** right at your lot\n• Touch-ups and reconditioning to keep inventory showroom-ready\n• Volume pricing for regular partnerships\n• Fast turnaround so units get to the front line quicker\n\nWe currently partner with dealerships across the High Desert. Want to set up a partnership? Call Ryan directly at **(760) 555-0199** or email **info@desertshieldautopaint.com**.`
    },

    about: {
      patterns: /\b(about|who|ryan|owner|experience|background|how long|history|qualif)\b/i,
      reply: `Desert Shield Auto Paint was founded by **Ryan Graham**, a seasoned pro with **15+ years** of experience in the auto paint and collision repair industry. 💪\n\nRyan has worked for several of the largest collision and auto paint companies in the country, and now he's bringing that expert-level craftsmanship directly to you.\n\nBased in **Victorville, CA**, we proudly serve the entire High Desert region with both mobile and shop services.`
    },

    photo: {
      patterns: /\b(photo|picture|image|pic|show|send|upload|attach|camera)\b/i,
      reply: `Great idea! Photos help us give you a much more accurate estimate. 📸\n\nYou can:\n1. **Upload right here** — click the 📎 button below to share photos in this chat\n2. **Use the quote form** — scroll down to our Free Quote section to upload photos with your vehicle details\n\nTry to get clear, well-lit photos showing:\n• The full damaged area\n• A close-up of the damage\n• The overall vehicle for context\n\nOnce we see the damage, we can tell you if it's a mobile or shop job and give you a price!`
    },

    thanks: {
      patterns: /\b(thank|thanks|thx|appreciate|helpful|awesome|great|perfect|cool)\b/i,
      reply: `You're welcome! 😊 Glad I could help.\n\nWhenever you're ready, you can:\n• **Submit a free quote** using the form below\n• **Call Ryan** at (760) 555-0199\n• **Email us** at info@desertshieldautopaint.com\n\nWe look forward to helping you out!`
    },

    contact: {
      patterns: /\b(call|phone|email|contact|reach|talk to|speak|number)\b/i,
      reply: `Here's how to reach us:\n\n📞 **Phone:** (760) 555-0199\n📧 **Email:** info@desertshieldautopaint.com\n🕗 **Hours:** Mon–Sat, 8:00 AM – 6:00 PM\n📍 **Location:** Victorville, CA (serving the whole High Desert)\n\nOr submit a **free quote request** using the form below — Ryan will get back to you within hours!`
    },

    warranty: {
      patterns: /\b(warrant|guarantee|stand behind|quality|promise|if it|come back|redo)\b/i,
      reply: `We stand behind our work! Desert Shield Auto Paint offers a **100% color match guarantee** on every job. 🛡️\n\nRyan's 15+ years of industry experience means you're getting expert-level craftsmanship — the same quality you'd find at the top national shops, but with the personal attention of a local business.\n\nIf you're ever not satisfied, we'll make it right. That's the Desert Shield promise.`
    },

    time: {
      patterns: /\b(how long|turnaround|time|days|weeks|when|fast|quick|soon|wait)\b/i,
      reply: `Turnaround times depend on the job:\n\n🚗 **Mobile repairs** (scratches, touch-ups, minor): Usually **same day**, done in 1–3 hours on-site\n🔧 **Shop repairs** (collision, full panel): Typically **2–5 days** depending on severity\n🔧 **Full repaints/color changes**: Usually **5–10 days**\n\nCompare that to insurance timelines which can take **weeks**! We pride ourselves on getting your vehicle back to you fast.`
    },

    payment: {
      patterns: /\b(pay|payment|cash|card|credit|debit|finance|venmo|zelle|method)\b/i,
      reply: `We want to make payment as easy as possible. For specific payment methods accepted, give Ryan a call at **(760) 555-0199** and he can walk you through the options.\n\nRemember — our repairs are often **less than your insurance deductible**, so you save money right from the start!`
    }
  };

  // Image upload response
  const imageResponse = `Thanks for sharing that photo! 📸 I can see you've uploaded an image of the damage.\n\nFor the most accurate assessment, I'd recommend submitting this through our **quote form below** along with your vehicle details. Ryan will personally review the photos and get back to you with a free estimate — usually within a few hours.\n\nIn the meantime, can I answer any questions about our services or pricing?`;

  // Default fallback
  const defaultReply = `That's a great question! I want to make sure you get the best answer.\n\nHere's what I'd suggest:\n• **Submit a free quote** with photos using the form below — Ryan will review and respond personally\n• **Call us** at (760) 555-0199 for immediate assistance\n• **Email** info@desertshieldautopaint.com\n\nOr ask me about our **services**, **pricing**, **mobile vs. shop**, **service area**, or **why to skip insurance** — I'm happy to help with those!`;

  // State
  let uploadedImages = [];
  let isProcessing = false;
  let elements = {};

  function init() {
    elements = {
      messages: document.getElementById('chat-messages'),
      input: document.getElementById('chat-input'),
      sendBtn: document.getElementById('chat-send-btn'),
      uploadBtn: document.getElementById('chat-upload-btn'),
      uploadInput: document.getElementById('chat-upload-input'),
      uploadPreview: document.getElementById('chat-upload-preview'),
      typingIndicator: document.getElementById('typing-indicator'),
      quickActions: document.querySelectorAll('.quick-action-btn'),
    };

    if (!elements.messages) return;

    elements.sendBtn.addEventListener('click', sendMessage);
    elements.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    elements.input.addEventListener('input', () => {
      elements.input.style.height = 'auto';
      elements.input.style.height = Math.min(elements.input.scrollHeight, 80) + 'px';
    });

    elements.uploadBtn.addEventListener('click', () => elements.uploadInput.click());
    elements.uploadInput.addEventListener('change', handleImageUpload);

    elements.quickActions.forEach(btn => {
      btn.addEventListener('click', () => {
        elements.input.value = btn.textContent.trim();
        sendMessage();
      });
    });

    addBotMessage("Hey there! 👋 I'm the Desert Shield Auto Paint assistant. I can help you with info about our services, pricing estimates, or getting a quote. What can I help you with today?");
  }

  function classifyMessage(text) {
    const msg = text.toLowerCase().trim();

    // Check each response category
    for (const [key, data] of Object.entries(responses)) {
      if (data.patterns.test(msg)) {
        return data.reply;
      }
    }

    return defaultReply;
  }

  function sendMessage() {
    const text = elements.input.value.trim();
    if ((!text && uploadedImages.length === 0) || isProcessing) return;

    isProcessing = true;
    const hasImages = uploadedImages.length > 0;

    addUserMessage(text, hasImages ? [...uploadedImages] : null);

    elements.input.value = '';
    elements.input.style.height = 'auto';
    clearImagePreviews();

    showTyping();

    // Simulate natural typing delay (600-1400ms)
    const delay = 600 + Math.random() * 800;

    setTimeout(() => {
      hideTyping();

      let reply;
      if (hasImages) {
        reply = imageResponse;
      } else {
        reply = classifyMessage(text);
      }

      addBotMessage(reply);
      isProcessing = false;
    }, delay);
  }

  function addBotMessage(text) {
    const div = document.createElement('div');
    div.className = 'chat-message bot';
    div.innerHTML = `
      <div class="msg-avatar">
        <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <div class="msg-bubble">${formatMessage(text)}</div>
    `;
    elements.messages.appendChild(div);
    scrollToBottom();
  }

  function addUserMessage(text, images) {
    const div = document.createElement('div');
    div.className = 'chat-message user';

    let imagesHtml = '';
    if (images && images.length > 0) {
      imagesHtml = `<div class="chat-image-preview">
        ${images.map(img => `<img src="${img.dataUrl}" alt="Uploaded photo">`).join('')}
      </div>`;
    }

    div.innerHTML = `
      <div class="msg-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      </div>
      <div class="msg-bubble">
        ${text ? formatMessage(text) : ''}
        ${imagesHtml}
        ${!text && images ? '<em>Shared photo(s)</em>' : ''}
      </div>
    `;
    elements.messages.appendChild(div);
    scrollToBottom();
  }

  function formatMessage(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  function showTyping() {
    elements.typingIndicator.classList.add('active');
    scrollToBottom();
  }

  function hideTyping() {
    elements.typingIndicator.classList.remove('active');
  }

  function scrollToBottom() {
    elements.messages.scrollTop = elements.messages.scrollHeight;
  }

  /* ---------- Image Upload ---------- */
  function handleImageUpload(e) {
    const files = Array.from(e.target.files);
    processFiles(files);
    e.target.value = '';
  }

  function processFiles(files) {
    for (const file of files) {
      if (uploadedImages.length >= MAX_IMAGES) {
        alert(`Maximum ${MAX_IMAGES} images allowed.`);
        break;
      }
      if (!ACCEPTED_TYPES.includes(file.type)) {
        alert('Please upload JPG or PNG images only.');
        continue;
      }
      if (file.size > MAX_FILE_SIZE) {
        alert('Image must be under 10MB.');
        continue;
      }

      const reader = new FileReader();
      reader.onload = (ev) => {
        const dataUrl = ev.target.result;
        uploadedImages.push({
          dataUrl,
          type: file.type,
          name: file.name,
        });
        renderImagePreviews();
      };
      reader.readAsDataURL(file);
    }
  }

  function renderImagePreviews() {
    elements.uploadPreview.innerHTML = '';
    if (uploadedImages.length === 0) {
      elements.uploadPreview.classList.remove('active');
      return;
    }
    elements.uploadPreview.classList.add('active');
    uploadedImages.forEach((img, idx) => {
      const thumb = document.createElement('div');
      thumb.className = 'chat-preview-thumb';
      thumb.innerHTML = `
        <img src="${img.dataUrl}" alt="${img.name}">
        <button class="remove-thumb" data-idx="${idx}">&times;</button>
      `;
      thumb.querySelector('.remove-thumb').addEventListener('click', () => {
        uploadedImages.splice(idx, 1);
        renderImagePreviews();
      });
      elements.uploadPreview.appendChild(thumb);
    });
  }

  function clearImagePreviews() {
    uploadedImages = [];
    elements.uploadPreview.innerHTML = '';
    elements.uploadPreview.classList.remove('active');
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => {
  ChatAssistant.init();
});
