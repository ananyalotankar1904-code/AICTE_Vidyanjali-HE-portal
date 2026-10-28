export type Language = 'en' | 'hi';

export const translations: Record<string, Record<Language, string>> = {
  // Navigation & Shell
  'cycle_demo': {
    en: '✧   Cycle 2026–27 · Illustrative Demo',
    hi: '✧   सत्र 2026–27 · सांकेतिक डेमो',
  },
  'workspace': {
    en: 'Workspace',
    hi: 'कार्यक्षेत्र',
  },
  'demo_workspace': {
    en: 'Demo workspace',
    hi: 'डेमो कार्यक्षेत्र',
  },
  'simulated_switcher': {
    en: 'Simulated role switcher · no production authentication',
    hi: 'सिम्युलेटेड भूमिका चयनकर्ता · कोई वास्तविक प्रमाणीकरण नहीं',
  },
  'footer_disclaimer': {
    en: 'Illustrative prototype · Synthetic demo records · No official submission, booking or decision is made.',
    hi: 'सांकेतिक प्रोटोटाइप · कृत्रिम डेमो रिकॉर्ड · कोई आधिकारिक प्रस्तुति, बुकिंग या निर्णय नहीं लिया गया है।',
  },

  // Applicant Dashboard
  'applicant_greeting': {
    en: 'Good morning, Applicant',
    hi: 'शुभ प्रभात, आवेदक',
  },
  'applicant_subtitle': {
    en: 'Your application, upcoming events and next steps — all in one place.',
    hi: 'आपका आवेदन, आगामी कार्यक्रम और अगले चरण — सभी एक ही स्थान पर।',
  },
  'open_my_app': {
    en: 'Open my application',
    hi: 'मेरा आवेदन खोलें',
  },
  'action_needed_deficiency_title': {
    en: 'Action needed: respond to an open deficiency',
    hi: 'कार्रवाई आवश्यक: खुली कमी (त्रुटि) का उत्तर दें',
  },
  'action_needed_deficiency_desc': {
    en: 'Provide the requested evidence by 12 November 2026. A deficiency is not a rejection.',
    hi: '12 नवंबर 2026 तक आवश्यक साक्ष्य प्रस्तुत करें। कमी का अर्थ अस्वीकृति नहीं है।',
  },
  'review_notice': {
    en: 'Review notice →',
    hi: 'सूचना देखें →',
  },
  'my_applications': {
    en: 'My applications',
    hi: 'मेरे आवेदन',
  },
  'cycle_badge': {
    en: '2026–27 cycle',
    hi: '2026–27 सत्र',
  },
  'current_stage': {
    en: 'Current stage',
    hi: 'वर्तमान चरण',
  },
  'scrutiny': {
    en: 'Scrutiny',
    hi: 'संवीक्षा (Scrutiny)',
  },
  'in_progress': {
    en: 'In progress',
    hi: 'प्रगति पर',
  },
  'documents_ready': {
    en: 'Documents ready',
    hi: 'दस्तावेज़ तैयार',
  },
  'meeting_docs_verified': {
    en: 'Meeting documents verified',
    hi: 'बैठक दस्तावेज़ सत्यापित',
  },
  'open_deficiencies': {
    en: 'Open deficiencies',
    hi: 'खुली कमियां (त्रुटियां)',
  },
  'response_due_date': {
    en: 'Response due 12 Nov',
    hi: 'उत्तर 12 नवंबर तक देय',
  },
  'my_application_card': {
    en: 'My application',
    hi: 'मेरा आवेदन',
  },
  'in_scrutiny_badge': {
    en: 'In scrutiny',
    hi: 'संवीक्षाधीन',
  },
  'synthetic_demo_badge': {
    en: 'Synthetic demo',
    hi: 'सांकेतिक डेमो',
  },
  'app_type_eoa': {
    en: 'Application type: Extension of approval',
    hi: 'आवेदन प्रकार: अनुमोदन का विस्तार (EoA)',
  },
  'owner_scrutiny_officer': {
    en: 'Owner: Scrutiny Officer',
    hi: 'प्रभारी: संवीक्षा अधिकारी',
  },
  'evc_notice': {
    en: 'EVC and committee review are applicable only when required by the configured route.',
    hi: 'ईवीसी (EVC) और समिति समीक्षा केवल तभी लागू होती है जब विन्यास मार्ग द्वारा आवश्यक हो।',
  },
  'next_action': {
    en: 'Next action',
    hi: 'अगला कदम',
  },
  'next_action_desc': {
    en: 'Respond to the deficiency and prepare meeting documents.',
    hi: 'कमी का उत्तर दें और संवीक्षा बैठक के दस्तावेज़ तैयार करें।',
  },
  'open_case': {
    en: 'Open case →',
    hi: 'मामला खोलें →',
  },
  'next_scheduled_event': {
    en: 'Next scheduled event',
    hi: 'अगला निर्धारित कार्यक्रम',
  },
  'online_scrutiny_meeting': {
    en: 'Online scrutiny meeting',
    hi: 'ऑनलाइन संवीक्षा बैठक',
  },
  'meeting_time_05': {
    en: '05 November 2026 · 11:00 AM IST · 45 min',
    hi: '05 नवंबर 2026 · पूर्वाह्न 11:00 बजे (IST) · 45 मिनट',
  },
  'meeting_time_06': {
    en: '06 November 2026 · 11:00 AM IST · 45 min',
    hi: '06 नवंबर 2026 · पूर्वाह्न 11:00 बजे (IST) · 45 मिनट',
  },
  'confirmed': {
    en: 'Confirmed',
    hi: 'पुष्टीकृत',
  },
  'rescheduled': {
    en: 'Rescheduled',
    hi: 'पुनर्निर्धारित',
  },
  'joining_link_na': {
    en: 'Joining link: Not available in supplied dataset.',
    hi: 'जुड़ने का लिंक: उपलब्ध डेटासेट में उपलब्ध नहीं है।',
  },
  'view_schedule': {
    en: 'View schedule',
    hi: 'समय-सारणी देखें',
  },
  'request_rescheduling': {
    en: 'Request rescheduling',
    hi: 'पुनर्निर्धारण अनुरोध',
  },
  'reschedule_requested_notice': {
    en: 'Reschedule requested · original appointment retained.',
    hi: 'पुनर्निर्धारण का अनुरोध किया गया · मूल नियुक्ति यथावत बनी रहेगी।',
  },
  'prep_checklist': {
    en: 'Preparation checklist',
    hi: 'तैयारी चेकलिस्ट',
  },
  'confirm_reps': {
    en: 'Confirm your representatives',
    hi: 'अपने प्रतिनिधियों की पुष्टि करें',
  },
  'reps_desc': {
    en: 'Principal and authorised representative',
    hi: 'प्राचार्य एवं अधिकृत प्रतिनिधि',
  },
  'todo': {
    en: 'To do',
    hi: 'अपूर्ण (बाकी)',
  },
  'complete_meeting_docs': {
    en: 'Complete meeting documents',
    hi: 'बैठक के दस्तावेज़ पूर्ण करें',
  },
  'review_docs_desc': {
    en: 'Review the documents requested for scrutiny',
    hi: 'संवीक्षा हेतु मांगे गए दस्तावेज़ों की जांच करें',
  },
  'view_docs': {
    en: 'View documents →',
    hi: 'दस्तावेज़ देखें →',
  },
  'review_deficiency_notice': {
    en: 'Review the deficiency notice',
    hi: 'कमी की सूचना की समीक्षा करें',
  },
  'response_due_12_nov': {
    en: 'Response due 12 November 2026',
    hi: 'उत्तर 12 नवंबर 2026 तक देय',
  },
  'respond': {
    en: 'Respond →',
    hi: 'उत्तर दें →',
  },
  'inst_profile': {
    en: 'Institution profile',
    hi: 'संस्थान प्रोफ़ाइल',
  },
  'inst_sub': {
    en: 'Synthetic institution · Maharashtra',
    hi: 'सांकेतिक संस्थान · महाराष्ट्र',
  },
  'inst_id': {
    en: 'Institution ID',
    hi: 'संस्थान आईडी',
  },
  'demo_account': {
    en: 'Demo account',
    hi: 'डेमो खाता',
  },
  'doc_readiness': {
    en: 'Document readiness',
    hi: 'दस्तावेज़ तैयारी',
  },
  'doc_verified_summary': {
    en: 'verified',
    hi: 'सत्यापित',
  },
  'doc_missing_note': {
    en: 'One required document is missing; others are awaiting review.',
    hi: 'एक आवश्यक दस्तावेज़ अनुपलब्ध है; अन्य समीक्षाधीन हैं।',
  },
  'manage_docs': {
    en: 'Manage documents →',
    hi: 'दस्तावेज़ प्रबंधित करें →',
  },
  'upcoming_deadlines': {
    en: 'Upcoming deadlines',
    hi: 'आगामी समय-सीमाएं',
  },
  'deficiency_response': {
    en: 'Deficiency response',
    hi: 'कमी निवारण उत्तर',
  },
  'due_soon': {
    en: 'Due soon',
    hi: 'शीघ्र देय',
  },
  'meeting_prep': {
    en: 'Meeting preparation',
    hi: 'बैठक की तैयारी',
  },
  'before_05_nov': {
    en: 'Before 05 November 2026',
    hi: '05 नवंबर 2026 से पूर्व',
  },
  'upcoming': {
    en: 'Upcoming',
    hi: 'आगामी',
  },
  'notifications': {
    en: 'Notifications',
    hi: 'सूचनाएं',
  },
  'meeting_confirmed_notif': {
    en: 'Scrutiny meeting confirmed',
    hi: 'संवीक्षा बैठक की पुष्टि हुई',
  },
  'today_linked': {
    en: 'Today · Linked to',
    hi: 'आज · संबद्ध मामला',
  },
  'unread': {
    en: 'Unread',
    hi: 'अपठित',
  },
  'read': {
    en: 'Read',
    hi: 'पठित',
  },
  'view_notifications': {
    en: 'View notifications →',
    hi: 'सूचनाएं देखें →',
  },

  // Steps
  'step_submitted': { en: 'Submitted', hi: 'प्रस्तुत' },
  'step_validation': { en: 'Validation', hi: 'सत्यापन' },
  'step_scrutiny': { en: 'Scrutiny', hi: 'संवीक्षा' },
  'step_review': { en: 'Review', hi: 'समीक्षा' },
  'step_decision': { en: 'Decision', hi: 'निर्णय' },

  // Scrutiny Officer Dashboard
  'scrutiny_overview': {
    en: 'Scrutiny overview',
    hi: 'संवीक्षा अवलोकन',
  },
  'scrutiny_sub': {
    en: 'Manage your scrutiny officer work queue for the 2026–27 cycle.',
    hi: '2026–27 सत्र के लिए अपनी संवीक्षा अधिकारी कार्य-पंक्ति प्रबंधित करें।',
  },
  'open_app_registry': {
    en: 'Open application registry',
    hi: 'आवेदन पंजी खोलें',
  },
  'case_attention_title': {
    en: 'A case needs your attention',
    hi: 'एक मामले में आपके ध्यान की आवश्यकता है',
  },
  'case_attention_desc': {
    en: 'Review the linked case and its approaching deadline.',
    hi: 'संबद्ध मामले और उसकी निकट आती समय-सीमा की समीक्षा करें।',
  },
  'pending_scrutiny': {
    en: 'Pending scrutiny',
    hi: 'संवीक्षा हेतु लंबित',
  },
  'pending_rescrutiny': {
    en: 'Pending re-scrutiny',
    hi: 'पुनः संवीक्षा हेतु लंबित',
  },
  'meetings_today': {
    en: 'Meetings today',
    hi: 'आज की बैठकें',
  },
  'needs_attention': {
    en: 'Needs attention',
    hi: 'ध्यानाकर्षण आवश्यक',
  },
  'illustrative_demo': {
    en: 'Illustrative demo',
    hi: 'सांकेतिक डेमो',
  },
  'my_work_queue': {
    en: 'My work queue',
    hi: 'मेरी कार्य-पंक्ति',
  },
  'work_queue_desc': {
    en: 'A focused view of assigned illustrative cases.',
    hi: 'आवंटित सांकेतिक मामलों का केंद्रित दृश्य।',
  },
  'th_app_inst': {
    en: 'Application / institution',
    hi: 'आवेदन / संस्थान',
  },
  'th_stage_owner': {
    en: 'Stage & owner',
    hi: 'चरण एवं प्रभारी',
  },
  'th_readiness': {
    en: 'Readiness',
    hi: 'दस्तावेज़ स्थिति',
  },
  'th_deadline_slot': {
    en: 'Deadline / slot',
    hi: 'समय-सीमा / स्लॉट',
  },
  'th_next_action': {
    en: 'Next action',
    hi: 'अगली कार्रवाई',
  },
  'todays_schedule': {
    en: 'Today’s schedule',
    hi: 'आज का कार्यक्रम',
  },
  'open_scheduling': {
    en: 'Open scheduling →',
    hi: 'समय-निर्धारण खोलें →',
  },
  'view_deadlines': {
    en: 'View deadlines →',
    hi: 'समय-सीमाएं देखें →',
  },
  'priority_actions': {
    en: 'Priority actions',
    hi: 'प्राथमिकता कार्रवाइयां',
  },
  'review_inst_response': {
    en: 'Review institution response',
    hi: 'संस्थान के उत्तर की समीक्षा करें',
  },
  'review_doc_readiness': {
    en: 'Review document readiness',
    hi: 'दस्तावेज़ तत्परता की समीक्षा करें',
  },
  'review_reschedule_request': {
    en: 'Review reschedule request',
    hi: 'पुनर्निर्धारण अनुरोध की समीक्षा करें',
  },
  'review_scrutiny_appt': {
    en: 'Review scrutiny appointment',
    hi: 'संवीक्षा नियुक्ति की समीक्षा करें',
  },
  'open_action': {
    en: 'Open →',
    hi: 'खोलें →',
  },
};

export const getTranslation = (key: string, lang: Language): string => {
  if (translations[key] && translations[key][lang]) {
    return translations[key][lang];
  }
  return key;
};

