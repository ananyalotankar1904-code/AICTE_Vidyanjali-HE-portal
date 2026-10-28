import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal, ROLES } from '../context/PortalContext';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    role,
    language,
    t,
    appId,
    institutionName,
    slotRescheduled,
    rescheduleRequested,
    deficiencyStatus,
    documents,
    openDialog,
    submitRescheduleRequest,
    showToast,
  } = usePortal();

  const isApplicant = role === ROLES[0];
  const isHi = language === 'hi';

  // Helper for Requesting Slot dialog
  const handleRequestSlot = () => {
    let reasonVal = '';
    let preferredVal = '';

    openDialog({
      title: isHi ? 'भिन्न समय-स्लॉट का अनुरोध करें' : 'Request a different slot',
      children: (
        <div>
          <p>
            {isHi
              ? 'मूल नियुक्ति तब तक पुष्टीकृत रहेगी जब तक नया समय स्वीकृत न हो जाए।'
              : 'The original appointment remains confirmed until a replacement is confirmed.'}
          </p>
          <label htmlFor="reason">{isHi ? 'कारण' : 'Reason'}</label>
          <textarea
            id="reason"
            placeholder={isHi ? 'विवरण दें कि अन्य समय की आवश्यकता क्यों है' : 'Describe why another time is needed'}
            onChange={(e) => {
              reasonVal = e.target.value;
            }}
          />
          <label htmlFor="preferred">{isHi ? 'पसंदीदा तिथि एवं समय' : 'Preferred date and time'}</label>
          <input
            id="preferred"
            type="datetime-local"
            onChange={(e) => {
              preferredVal = e.target.value;
            }}
          />
        </div>
      ),
      confirmLabel: isHi ? 'अनुरोध प्रस्तुत करें' : 'Submit mock request',
      notice: isHi ? 'यह कार्रवाई केवल स्थानीय डेमो स्थिति को बदलती है।' : 'This action changes local demo state only.',
      onConfirm: () => {
        if (!reasonVal || !preferredVal) {
          showToast(isHi ? 'कृपया कारण एवं पसंदीदा समय भरें।' : 'Add a reason and preferred time.');
          return;
        }
        submitRescheduleRequest(reasonVal, preferredVal);
      },
    });
  };

  // Reusable Event Component matching sih_final.html
  const renderEvent = () => (
    <div className="event">
      <div className="datebox">
        <small>{isHi ? 'नवंबर' : 'NOV'}</small>
        <b>{slotRescheduled ? '06' : '05'}</b>
      </div>
      <div>
        <strong>{t('online_scrutiny_meeting')}</strong>
        <p>
          {slotRescheduled ? t('meeting_time_06') : t('meeting_time_05')}
        </p>
        <span className="badge blue">
          {slotRescheduled ? t('rescheduled') : t('confirmed')}
        </span>{' '}
        <p>{t('joining_link_na')}</p>
      </div>
    </div>
  );

  // Reusable Progress Stepper matching sih_final.html
  const renderProgress = () => {
    const steps = [
      { key: 'step_submitted', label: t('step_submitted') },
      { key: 'step_validation', label: t('step_validation') },
      { key: 'step_scrutiny', label: t('step_scrutiny') },
      { key: 'step_review', label: t('step_review') },
      { key: 'step_decision', label: t('step_decision') },
    ];
    return (
      <>
        <div className="progress">
          {steps.map((s, i) => (
            <div
              key={s.key}
              className={`step ${i < 2 ? 'done' : i === 2 ? 'current' : ''}`}
            >
              <i>{i < 2 ? '✓' : i + 1}</i>
              {s.label}
            </div>
          ))}
        </div>
        <p className="notice">
          {t('evc_notice')}
        </p>
      </>
    );
  };

  // 1. APPLICANT DASHBOARD
  if (isApplicant) {
    const verifiedDocCount = Object.values(documents).filter((v) => v === 'Verified').length;
    const totalDocCount = Object.keys(documents).length;
    const openDeficiencyCount = deficiencyStatus === 'REVIEWED' ? 0 : 1;

    return (
      <div>
        <div className="pagehead">
          <div>
            <div className="eyebrow">{isHi ? 'एआईसीटीई अनुमोदन एवं अनुपालन' : 'AICTE APPROVAL & COMPLIANCE'}</div>
            <h1>{t('applicant_greeting')}</h1>
            <p>{t('applicant_subtitle')}</p>
          </div>
          <button className="btn primary" onClick={() => navigate('/case')}>
            {t('open_my_app')}
          </button>
        </div>

        <div className="banner">
          <span>⚑</span>
          <div style={{ flex: 1 }}>
            <strong>{t('action_needed_deficiency_title')}</strong>
            <p>{t('action_needed_deficiency_desc')}</p>
          </div>
          <button className="btn text" onClick={() => navigate('/deficiencies')}>
            {t('review_notice')}
          </button>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid metrics">
          <div className="card metric">
            <div className="label">{t('my_applications')}</div>
            <strong>1</strong>
            <small>{t('cycle_badge')}</small>
          </div>
          <div className="card metric">
            <div className="label">{t('current_stage')}</div>
            <strong>{t('scrutiny')}</strong>
            <small>{t('in_progress')}</small>
          </div>
          <div className="card metric">
            <div className="label">{t('documents_ready')}</div>
            <strong>
              {isHi
                ? `${totalDocCount} में से ${verifiedDocCount}`
                : `${verifiedDocCount} of ${totalDocCount}`}
            </strong>
            <small>{t('meeting_docs_verified')}</small>
          </div>
          <div className="card metric">
            <div className="label">{t('open_deficiencies')}</div>
            <strong>{openDeficiencyCount}</strong>
            <small>{t('response_due_date')}</small>
          </div>
        </div>

        {/* Columns Layout */}
        <div className="grid columns">
          {/* Left Stack */}
          <div className="stack">
            {/* My Application Card */}
            <section className="card">
              <div className="cardhead">
                <h2>{t('my_application_card')}</h2>
              </div>
              <div className="meta">
                <span>{appId}</span>
                <span className="badge blue">{t('in_scrutiny_badge')}</span>
                <span className="badge">{t('synthetic_demo_badge')}</span>
              </div>
              <div className="case-title">{institutionName}</div>
              <div className="meta">
                <span>{t('app_type_eoa')}</span>
                <span>{t('owner_scrutiny_officer')}</span>
              </div>
              {renderProgress()}
              <hr className="divider" />
              <div className="listrow">
                <div>
                  <strong>{t('next_action')}</strong>
                  <small>{t('next_action_desc')}</small>
                </div>
                <button className="btn text" onClick={() => navigate('/case')}>
                  {t('open_case')}
                </button>
              </div>
            </section>

            {/* Next Scheduled Event Card */}
            <section className="card">
              <div className="cardhead">
                <h2>{t('next_scheduled_event')}</h2>
              </div>
              {renderEvent()}
              <hr className="divider" />
              <div className="buttonrow">
                <button className="btn" onClick={() => navigate('/schedule')}>
                  {t('view_schedule')}
                </button>
                <button className="btn" onClick={handleRequestSlot}>
                  {t('request_rescheduling')}
                </button>
              </div>
              {rescheduleRequested && (
                <p className="notice">
                  {t('reschedule_requested_notice')}
                </p>
              )}
            </section>

            {/* Preparation Checklist */}
            <section className="card">
              <div className="cardhead">
                <h2>{t('prep_checklist')}</h2>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('confirm_reps')}</strong>
                  <small>{t('reps_desc')}</small>
                </div>
                <span className="badge amber">{t('todo')}</span>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('complete_meeting_docs')}</strong>
                  <small>{t('review_docs_desc')}</small>
                </div>
                <button className="btn text" onClick={() => navigate('/documents')}>
                  {t('view_docs')}
                </button>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('review_deficiency_notice')}</strong>
                  <small>{t('response_due_12_nov')}</small>
                </div>
                <button className="btn text" onClick={() => navigate('/deficiencies')}>
                  {t('respond')}
                </button>
              </div>
            </section>
          </div>

          {/* Right Stack */}
          <div className="stack">
            <section className="card">
              <div className="cardhead">
                <h2>{t('inst_profile')}</h2>
              </div>
              <strong>{institutionName}</strong>
              <p className="muted">{t('inst_sub')}</p>
              <div className="listrow">
                <div>
                  <small>{t('inst_id')}</small>
                  <strong>DEMO-INST-01</strong>
                </div>
                <span className="badge">{t('demo_account')}</span>
              </div>
            </section>

            <section className="card">
              <div className="cardhead">
                <h2>{t('doc_readiness')}</h2>
              </div>
              <strong>
                {isHi
                  ? `4 में से ${verifiedDocCount} सत्यापित`
                  : `${verifiedDocCount} of ${totalDocCount} verified`}
              </strong>
              <div className="bar">
                <span style={{ width: `${(verifiedDocCount / totalDocCount) * 100}%` }}></span>
              </div>
              <p className="muted">{t('doc_missing_note')}</p>
              <button className="btn text" onClick={() => navigate('/documents')}>
                {t('manage_docs')}
              </button>
            </section>

            <section className="card">
              <div className="cardhead">
                <h2>{t('upcoming_deadlines')}</h2>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('deficiency_response')}</strong>
                  <small>12 November 2026</small>
                </div>
                <span className="badge amber">{t('due_soon')}</span>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('meeting_prep')}</strong>
                  <small>{t('before_05_nov')}</small>
                </div>
                <span className="badge blue">{t('upcoming')}</span>
              </div>
            </section>

            <section className="card">
              <div className="cardhead">
                <h2>{t('notifications')}</h2>
              </div>
              <div className="listrow">
                <div>
                  <strong>{t('meeting_confirmed_notif')}</strong>
                  <small>{t('today_linked')} {appId}</small>
                </div>
                <span className="badge blue">{t('unread')}</span>
              </div>
              <button className="btn text" onClick={() => navigate('/notifications')}>
                {t('view_notifications')}
              </button>
            </section>
          </div>
        </div>
      </div>
    );
  }

  // 2. OFFICER DASHBOARDS
  const officerConfigs: Record<string, [string, string, string, string, string]> = {
    'Intake Officer': [
      'Intake overview',
      'New submissions',
      'Incomplete applications',
      'Awaiting validation',
      'Due-soon cases',
    ],
    'Scrutiny Officer': [
      isHi ? 'संवीक्षा अवलोकन' : 'Scrutiny overview',
      isHi ? 'संवीक्षा हेतु लंबित' : 'Pending scrutiny',
      isHi ? 'पुनः संवीक्षा हेतु लंबित' : 'Pending re-scrutiny',
      isHi ? 'खुली कमियां (त्रुटियां)' : 'Open deficiencies',
      isHi ? 'आज की बैठकें' : 'Meetings today',
    ],
    'EVC Coordinator': [
      'Inspection overview',
      'Needs scheduling',
      'Scheduled visits',
      'Reports pending',
      'Completed inspections',
    ],
    'Committee Secretariat': [
      'Committee overview',
      'Awaiting review',
      'Incomplete packs',
      'Scheduled reviews',
      'Clarifications',
    ],
    'Competent Authority Secretariat': [
      'Decision overview',
      'Ready for decision',
      'Unresolved prerequisites',
      'Outstanding conditions',
      'Recent decisions',
    ],
  };

  const config = officerConfigs[role] || officerConfigs['Scrutiny Officer'];
  const isCompetentAuthority = role === 'Competent Authority Secretariat';

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">{isHi ? 'एआईसीटीई अनुमोदन एवं अनुपालन' : 'AICTE APPROVAL & COMPLIANCE'}</div>
          <h1>{config[0]}</h1>
          <p>
            {role === 'Scrutiny Officer' && isHi
              ? t('scrutiny_sub')
              : `Manage your ${role.toLowerCase()} work queue for the 2026–27 cycle.`}
          </p>
        </div>
        <button className="btn" onClick={() => navigate('/applications')}>
          {t('open_app_registry')}
        </button>
      </div>

      <div className="banner">
        <span>⚑</span>
        <div style={{ flex: 1 }}>
          <strong>
            {isCompetentAuthority
              ? 'Decision controls are restricted'
              : t('case_attention_title')}
          </strong>
          <p>
            {isCompetentAuthority
              ? 'This demo does not grant authorization to make an official decision.'
              : t('case_attention_desc')}
          </p>
        </div>
        <button className="btn text" onClick={() => navigate('/case')}>
          {t('open_case')}
        </button>
      </div>

      {/* 4 Metrics */}
      <div className="grid metrics">
        {config.slice(1).map((title, i) => (
          <div key={title} className="card metric">
            <div className="label">{title}</div>
            <strong>1</strong>
            <small>{i === 3 ? t('illustrative_demo') : t('needs_attention')}</small>
          </div>
        ))}
      </div>

      {/* Columns */}
      <div className="grid columns">
        {/* Left Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>{t('my_work_queue')}</h2>
            </div>
            <p className="muted">{t('work_queue_desc')}</p>
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>{t('th_app_inst')}</th>
                    <th>{t('th_stage_owner')}</th>
                    <th>{t('th_readiness')}</th>
                    <th>{t('th_deadline_slot')}</th>
                    <th>{t('th_next_action')}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td data-label={t('th_app_inst')}>
                      <strong>{appId}</strong>
                      <small>{institutionName}</small>
                    </td>
                    <td data-label={t('th_stage_owner')}>
                      {t('scrutiny')}
                      <small>{role === 'Scrutiny Officer' && isHi ? 'संवीक्षा अधिकारी' : role}</small>
                    </td>
                    <td data-label={t('th_readiness')}>
                      <span className="badge amber">{isHi ? '4 में से 1 सत्यापित' : '1 of 4 verified'}</span>
                      <small>
                        {deficiencyStatus === 'RESPONSE_SUBMITTED'
                          ? (isHi ? 'उत्तर प्रस्तुत किया गया' : 'Response submitted')
                          : deficiencyStatus === 'REVIEWED'
                          ? (isHi ? 'उत्तर की समीक्षा हुई' : 'Response reviewed')
                          : (isHi ? 'कमी (त्रुटि) खुली है' : 'Deficiency open')}
                      </small>
                    </td>
                    <td data-label={t('th_deadline_slot')}>
                      12 Nov 2026
                      <small>{isHi ? 'बैठक 05 नवंबर' : 'Meeting 05 Nov'}</small>
                    </td>
                    <td data-label={t('th_next_action')}>
                      <button className="btn text" onClick={() => navigate('/case')}>
                        {t('open_case')}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>{t('todays_schedule')}</h2>
            </div>
            {renderEvent()}
            <hr className="divider" />
            <button
              className="btn text"
              onClick={() => navigate(role === 'EVC Coordinator' ? '/evc' : '/scheduling')}
            >
              {t('open_scheduling')}
            </button>
          </section>
        </div>

        {/* Right Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>{t('upcoming_deadlines')}</h2>
            </div>
            <div className="listrow">
              <div>
                <strong>{t('deficiency_response')}</strong>
                <small>{appId} · 12 Nov 2026</small>
              </div>
              <span className="badge amber">{t('due_soon')}</span>
            </div>
            <button className="btn text" onClick={() => navigate('/notifications')}>
              {t('view_deadlines')}
            </button>
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>{t('priority_actions')}</h2>
            </div>
            <div className="listrow">
              <div>
                <strong>
                  {deficiencyStatus === 'RESPONSE_SUBMITTED'
                    ? t('review_inst_response')
                    : t('review_doc_readiness')}
                </strong>
                <small>{institutionName}</small>
              </div>
              <button className="btn text" onClick={() => navigate('/deficiencies')}>
                {t('open_action')}
              </button>
            </div>
            <div className="listrow">
              <div>
                <strong>
                  {rescheduleRequested
                    ? t('review_reschedule_request')
                    : t('review_scrutiny_appt')}
                </strong>
                <small>{appId}</small>
              </div>
              <button className="btn text" onClick={() => navigate('/scheduling')}>
                {t('open_action')}
              </button>
            </div>
          </section>

          {isCompetentAuthority && (
            <section className="card">
              <div className="cardhead">
                <h2>Decision authorization</h2>
              </div>
              <p>
                Final decision controls require authorised production access. No statutory decision can be made in this demo.
              </p>
              <button className="btn" disabled>
                Issue decision · Restricted
              </button>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};
