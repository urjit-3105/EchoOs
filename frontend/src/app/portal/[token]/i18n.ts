export type Language = "en" | "es" | "fr" | "de" | "hi";

export interface PortalTranslations {
  onboarding: string;
  welcomeUser: string;
  steps: {
    welcome: string;
    personalInfo: string;
    documents: string;
    review: string;
  };
  step1: {
    title: string;
    desc: string;
    getStarted: string;
  };
  step2: {
    title: string;
    fullName: string;
    email: string;
    phone: string;
    address: string;
    addressPlaceholder: string;
    saveAndContinue: string;
    saving: string;
  };
  step3: {
    title: string;
    govId: string;
    govIdDesc: string;
    uploaded: string;
    upload: string;
    uploading: string;
    offerLetter: string;
    offerLetterDesc: string;
    saveAndContinue: string;
  };
  step4: {
    title: string;
    desc: string;
    agreeTerms: string;
    completeOnboarding: string;
    submitting: string;
  };
  step5: {
    title: string;
    desc: string;
  };
  invalid: {
    title: string;
    desc: string;
  };
}

export const translations: Record<Language, PortalTranslations> = {
  en: {
    onboarding: "Onboarding",
    welcomeUser: "Welcome",
    steps: {
      welcome: "Welcome",
      personalInfo: "Personal Info",
      documents: "Documents",
      review: "Review",
    },
    step1: {
      title: "Welcome to {org}!",
      desc: "We're excited to have you on board. This onboarding portal will guide you through setting up your profile, signing necessary documents, and preparing for your first day.",
      getStarted: "Get Started",
    },
    step2: {
      title: "Personal Details",
      fullName: "Full Name",
      email: "Email",
      phone: "Phone Number",
      address: "Home Address",
      addressPlaceholder: "123 Main St, City, Country",
      saveAndContinue: "Save & Continue",
      saving: "Saving...",
    },
    step3: {
      title: "Upload Documents",
      govId: "Government ID",
      govIdDesc: "Required for compliance",
      uploaded: "Uploaded",
      upload: "Upload",
      uploading: "Uploading...",
      offerLetter: "Offer Letter (Signed)",
      offerLetterDesc: "Completed via Docusign",
      saveAndContinue: "Save & Continue",
    },
    step4: {
      title: "Review & Submit",
      desc: "By submitting your onboarding profile, our automated systems will begin provisioning your accounts and equipment.",
      agreeTerms: "I agree to the company policies and terms.",
      completeOnboarding: "Complete Onboarding",
      submitting: "Submitting...",
    },
    step5: {
      title: "You're all set!",
      desc: "Your onboarding is complete. Our AI agents are currently configuring your accounts and setting up your workspace. You will receive an email shortly with your credentials.",
    },
    invalid: {
      title: "Invalid or Expired Invitation",
      desc: "This onboarding link is no longer valid. Please contact your manager or HR administrator.",
    },
  },
  es: {
    onboarding: "Incorporación",
    welcomeUser: "Bienvenido/a",
    steps: {
      welcome: "Bienvenida",
      personalInfo: "Datos Personales",
      documents: "Documentos",
      review: "Revisión",
    },
    step1: {
      title: "¡Bienvenido/a a {org}!",
      desc: "Estamos encantados de tenerte en el equipo. Este portal te guiará para configurar tu perfil, firmar documentos y preparar tu primer día.",
      getStarted: "Comenzar",
    },
    step2: {
      title: "Detalles Personales",
      fullName: "Nombre Completo",
      email: "Correo Electrónico",
      phone: "Número de Teléfono",
      address: "Dirección de Residencia",
      addressPlaceholder: "Calle Principal 123, Ciudad, País",
      saveAndContinue: "Guardar y Continuar",
      saving: "Guardando...",
    },
    step3: {
      title: "Cargar Documentos",
      govId: "Identificación Oficial",
      govIdDesc: "Requerido para cumplimiento legal",
      uploaded: "Cargado",
      upload: "Subir",
      uploading: "Subiendo...",
      offerLetter: "Carta de Oferta (Firmada)",
      offerLetterDesc: "Completado mediante Docusign",
      saveAndContinue: "Guardar y Continuar",
    },
    step4: {
      title: "Revisar y Enviar",
      desc: "Al enviar tu perfil, nuestros sistemas automatizados comenzarán a aprovisionar tus cuentas y accesos.",
      agreeTerms: "Acepto las políticas y términos de la empresa.",
      completeOnboarding: "Finalizar Incorporación",
      submitting: "Enviando...",
    },
    step5: {
      title: "¡Todo Listo!",
      desc: "Tu proceso de incorporación ha finalizado. Nuestros agentes de IA están aprovisionando tus cuentas. En breve recibirás un correo con tus credenciales.",
    },
    invalid: {
      title: "Invitación Inválida o Expirada",
      desc: "Este enlace de incorporación ya no es válido. Comuníquese con su administrador de RRHH.",
    },
  },
  fr: {
    onboarding: "Intégration",
    welcomeUser: "Bienvenue",
    steps: {
      welcome: "Bienvenue",
      personalInfo: "Infos Personnelles",
      documents: "Documents",
      review: "Vérification",
    },
    step1: {
      title: "Bienvenue chez {org} !",
      desc: "Nous sommes ravis de vous accueillir. Ce portail vous accompagnera pour configurer votre profil, signer les documents requis et préparer votre arrivée.",
      getStarted: "Commencer",
    },
    step2: {
      title: "Coordonnées Personnelles",
      fullName: "Nom Complet",
      email: "Adresse E-mail",
      phone: "Numéro de Téléphone",
      address: "Adresse Domicile",
      addressPlaceholder: "123 Rue Principale, Ville, Pays",
      saveAndContinue: "Enregistrer & Continuer",
      saving: "Enregistrement...",
    },
    step3: {
      title: "Téléverser les Documents",
      govId: "Pièce d'Identité Officielle",
      govIdDesc: "Requis pour la conformité",
      uploaded: "Téléversé",
      upload: "Téléverser",
      uploading: "En cours...",
      offerLetter: "Lettre d'Offre (Signée)",
      offerLetterDesc: "Signée via Docusign",
      saveAndContinue: "Enregistrer & Continuer",
    },
    step4: {
      title: "Vérifier & Valider",
      desc: "En soumettant votre profil, nos agents IA initialiseront automatiquement vos comptes et outils.",
      agreeTerms: "J'accepte les conditions et règlements de l'entreprise.",
      completeOnboarding: "Finaliser l'Intégration",
      submitting: "Validation en cours...",
    },
    step5: {
      title: "Tout est Prêt !",
      desc: "Votre intégration est terminée. Nos agents d'IA configurent vos accès. Vous recevrez bientôt un e-mail avec vos identifiants.",
    },
    invalid: {
      title: "Invitation Invalide ou Expirée",
      desc: "Ce lien d'intégration n'est plus valide. Veuillez contacter votre responsable RH.",
    },
  },
  de: {
    onboarding: "Einführung",
    welcomeUser: "Willkommen",
    steps: {
      welcome: "Willkommen",
      personalInfo: "Persönliche Daten",
      documents: "Dokumente",
      review: "Überprüfung",
    },
    step1: {
      title: "Willkommen bei {org}!",
      desc: "Wir freuen uns, Sie im Team zu haben. Dieses Portal leitet Sie durch die Einrichtung Ihres Profils und aller erforderlichen Dokumente.",
      getStarted: "Jetzt Starten",
    },
    step2: {
      title: "Persönliche Angaben",
      fullName: "Vollständiger Name",
      email: "E-Mail-Adresse",
      phone: "Telefonnummer",
      address: "Wohnadresse",
      addressPlaceholder: "Hauptstraße 123, Stadt, Land",
      saveAndContinue: "Speichern & Weiter",
      saving: "Wird gespeichert...",
    },
    step3: {
      title: "Dokumente Hochladen",
      govId: "Amtlicher Lichtbildausweis",
      govIdDesc: "Erforderlich für Compliance",
      uploaded: "Hochgeladen",
      upload: "Hochladen",
      uploading: "Lädt hoch...",
      offerLetter: "Vertragsangebot (Unterzeichnet)",
      offerLetterDesc: "Über Docusign abgeschlossen",
      saveAndContinue: "Speichern & Weiter",
    },
    step4: {
      title: "Prüfen & Absenden",
      desc: "Mit dem Absenden Ihres Profils beginnen unsere KI-Agenten mit der Bereitstellung Ihrer Benutzerkonten.",
      agreeTerms: "Ich stimme den Unternehmensrichtlinien und Bedingungen zu.",
      completeOnboarding: "Einführung Abschließen",
      submitting: "Wird übermittelt...",
    },
    step5: {
      title: "Alles Erledigt!",
      desc: "Ihr Onboarding ist abgeschlossen. Unsere KI-Agenten konfigurieren jetzt Ihre Konten. Sie erhalten in Kürze eine E-Mail mit Ihren Zugangsdaten.",
    },
    invalid: {
      title: "Ungültige oder Abgelaufene Einladung",
      desc: "Dieser Link ist nicht mehr gültig. Bitte wenden Sie sich an Ihren Personalverantwortlichen.",
    },
  },
  hi: {
    onboarding: "ऑनबोर्डिंग",
    welcomeUser: "नमस्ते",
    steps: {
      welcome: "स्वागत",
      personalInfo: "व्यक्तिगत जानकारी",
      documents: "दस्तावेज़",
      review: "समीक्षा",
    },
    step1: {
      title: "{org} में आपका स्वागत है!",
      desc: "टीम में आपका स्वागत करते हुए हमें बेहद खुशी है। यह पोर्टल आपकी प्रोफ़ाइल सेट करने और आवश्यक दस्तावेज़ जमा करने में मदद करेगा।",
      getStarted: "शुरू करें",
    },
    step2: {
      title: "व्यक्तिगत विवरण",
      fullName: "पूरा नाम",
      email: "ईमेल",
      phone: "फ़ोन नंबर",
      address: "घर का पता",
      addressPlaceholder: "123 मुख्य मार्ग, शहर, देश",
      saveAndContinue: "सहेजें और आगे बढ़ें",
      saving: "सहेजा जा रहा है...",
    },
    step3: {
      title: "दस्तावेज़ अपलोड करें",
      govId: "सरकारी पहचान पत्र",
      govIdDesc: "अनुपालन के लिए आवश्यक",
      uploaded: "अपलोड किया गया",
      upload: "अपलोड करें",
      uploading: "अपलोड हो रहा है...",
      offerLetter: "प्रस्ताव पत्र (हस्ताक्षरित)",
      offerLetterDesc: "DocuSign द्वारा सत्यापित",
      saveAndContinue: "सहेजें और आगे बढ़ें",
    },
    step4: {
      title: "समीक्षा और जमा करें",
      desc: "ऑनबोर्डिंग प्रोफ़ाइल जमा करने के बाद, हमारे AI एजेंट आपके खाते और उपकरण स्वचालित रूप से तैयार करेंगे।",
      agreeTerms: "मैं कंपनी की नीतियों और शर्तों से सहमत हूँ।",
      completeOnboarding: "ऑनबोर्डिंग पूरी करें",
      submitting: "जमा किया जा रहा है...",
    },
    step5: {
      title: "सब कुछ तैयार है!",
      desc: "आपकी ऑनबोर्डिंग सफलतापूर्वक पूरी हो गई है। हमारे AI एजेंट आपके खाते सक्रिय कर रहे हैं। शीघ्र ही आपको क्रेडेंशियल प्राप्त होंगे।",
    },
    invalid: {
      title: "अमान्य या समाप्त लिंक",
      desc: "यह ऑनबोर्डिंग लिंक अब मान्य नहीं है। कृपया अपने एचआर व्यवस्थापक से संपर्क करें।",
    },
  },
};
