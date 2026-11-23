/* =========================================================
   CONFIGURACIÓN DEL SITIO — edita este archivo, no requiere programar.
   ========================================================= */
window.BRL_CONFIG = {
  // Datos de contacto que aparecen en todo el sitio
  email: "info@thebusinessresearchlab.com",
  emailDirecto: "rafaelalfonso1@gmail.com",       // correo directo (sección Contacto) — deja "" para ocultarlo
  phone: "+1 (809) 853-7113",                     // ej. "+1 (809) 555-0123" — deja "" para ocultarlo
  whatsapp: "",                                   // solo dígitos, ej. "18095550123" — deja "" para ocultarlo
  location: "Santo Domingo, República Dominicana",
  linkedin: "",                                   // URL completa — deja "" para ocultarlo

  // Enlaces de pago de las membresías (Stripe Payment Links, Lemon Squeezy, Gumroad, etc.)
  // Si lo dejas "", el botón abre el formulario de contacto con el plan preseleccionado.
  plans: {
    pulse:        { checkoutUrl: "" },  // Boletín gratis — puede apuntar a Mailchimp/Substack
    professional: { checkoutUrl: "" },  // e.g. "https://buy.stripe.com/xxxx"
    enterprise:   { checkoutUrl: "" }   // normalmente vacío → va al formulario de contacto
  }
};
