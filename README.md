# Desert Shield Auto Paint — Website

Professional single-page website for Desert Shield Auto Paint, a mobile auto paint and body repair business serving the High Desert region of Southern California.

## Features

- **Dark premium automotive theme** — responsive, mobile-first design
- **AI Chat Assistant** — powered by Google Gemini API with image upload support
- **Quote Request Form** — with drag & drop image upload and email notifications via EmailJS
- **Insurance comparison** — side-by-side breakdown of direct repair vs. insurance
- **Particle animation** — ambient hero section with canvas-based particles
- **Scroll animations** — reveal-on-scroll effects throughout

## Quick Start

1. Clone or download this project
2. Open `index.html` in a browser — the site works as a static site with no build step

### For AI Chat & Email Notifications

3. Copy `.env.example` to reference your keys
4. Edit the `<script>` config block in `index.html`:

```html
<script>
  window.GEMINI_API_KEY = 'your_gemini_api_key';
  window.EMAILJS_SERVICE_ID = 'your_service_id';
  window.EMAILJS_TEMPLATE_ID = 'your_template_id';
  window.EMAILJS_PUBLIC_KEY = 'your_public_key';
</script>
```

### API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| Google Gemini | AI chat assistant | [Google AI Studio](https://aistudio.google.com/apikey) |
| EmailJS | Quote form email notifications | [emailjs.com](https://www.emailjs.com/) |

## EmailJS Setup

1. Create a free account at [emailjs.com](https://www.emailjs.com/)
2. Add an email service (Gmail, Outlook, etc.)
3. Create an email template with these variables:
   - `{{customer_name}}` — Customer's name
   - `{{customer_phone}}` — Phone number
   - `{{customer_email}}` — Email address
   - `{{vehicle_info}}` — Year/Make/Model
   - `{{vehicle_color}}` — Vehicle color
   - `{{service_type}}` — Selected service
   - `{{damage_description}}` — Damage description
   - `{{image_count}}` — Number of photos uploaded
   - `{{submission_time}}` — When the form was submitted
4. Copy your Service ID, Template ID, and Public Key into the config

## Deployment

### GitHub Pages
1. Push to a GitHub repo
2. Go to Settings > Pages > Deploy from main branch

### Netlify
1. Drag the project folder to [netlify.com/drop](https://app.netlify.com/drop)
2. Set environment variables in Site Settings > Environment Variables

### Vercel
1. Import the repo at [vercel.com](https://vercel.com/)
2. Deploy — it auto-detects as a static site

## Project Structure

```
desert-shield/
├── index.html          Main single-page site
├── css/
│   └── styles.css      All styles (dark theme, responsive)
├── js/
│   ├── main.js         Navigation, particles, scroll animations
│   ├── chat.js         Gemini AI chat with image upload
│   ├── form.js         Quote form, validation, image upload
│   └── notifications.js EmailJS email notifications
├── assets/             Images and icons (add as needed)
├── .env.example        Environment variable reference
└── README.md           This file
```

## Tech Stack

- Vanilla HTML/CSS/JavaScript (no build tools required)
- Google Fonts (Oswald + Inter)
- Google Gemini API (AI chat)
- EmailJS (email notifications)
- Canvas API (particle animation)

## Contact (Placeholder)

- Phone: (760) 555-0199
- Email: info@desertshieldautopaint.com
- Location: Victorville, CA
- Hours: Mon-Sat 8:00 AM - 6:00 PM
