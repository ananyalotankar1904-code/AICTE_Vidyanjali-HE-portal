import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const CasePage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const {
    appId,
    institutionName,
    language,
    t,
    slotRescheduled,
    deficiencyStatus,
    documents,
    auditLogs,
    canonicalData,
  } = usePortal();

  const isHi = language === 'hi';
  const currentId = id || appId;

  // Find if it's in canonicalData
  const canonicalApp = canonicalData.applications.find((a: any) => a.application_id === currentId);
  const canonicalInst = canonicalApp
    ? (canonicalData.institutions as Record<string, any>)[canonicalApp.institution_id]
    : null;

  const displayInstName = canonicalInst ? canonicalInst.name : institutionName;
  const verifiedDocCount = Object.values(documents).filter((v) => v === 'Verified').length;
  const totalDocCount = Object.keys(documents).length;

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

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">{isHi ? 'एआईसीटीई अनुमोदन एवं अनुपालन' : 'AICTE APPROVAL & COMPLIANCE'}</div>
          <h1>{isHi ? 'आवेदन मामला फ़ाइल' : 'Application case file'}</h1>
          <p>{isHi ? 'प्रगति, साक्ष्य एवं गतिविधि का एकल दृश्य।' : 'A single view of progress, evidence and activity.'}</p>
        </div>
        <button className="btn" onClick={() => navigate('/schedule')}>
          {t('view_schedule')}
        </button>
      </div>

      <div className="card">
        <div className="meta">
          <span className="badge blue">{t('in_scrutiny_badge')}</span>
          <span className="badge amber">{t('needs_attention')}</span>
          <span>{currentId}</span>
        </div>
        <div className="case-title">{displayInstName}</div>
        <div className="meta">
          <span>{t('owner_scrutiny_officer')}</span>
          <span>{isHi ? 'लक्ष्य: 12 नवंबर 2026' : 'Target: 12 Nov 2026'}</span>
          <span>{isHi ? 'अगला: कमी का उत्तर दें' : 'Next: Respond to deficiency'}</span>
        </div>
        {renderProgress()}
      </div>

      <div className="grid columns" style={{ marginTop: '16px' }}>
        {/* Left Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>{isHi ? 'कार्यक्रम' : 'Events'}</h2>
            </div>
            {renderEvent()}
            <button className="btn text" onClick={() => navigate('/schedule')}>
              {isHi ? 'सभी कार्यक्रम देखें →' : 'View all events →'}
            </button>
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>{isHi ? 'दस्तावेज़ एवं कमियां' : 'Documents and deficiency'}</h2>
            </div>
            <p>
              {isHi
                ? `4 में से ${verifiedDocCount} संवीक्षा दस्तावेज़ सत्यापित। ${
                    deficiencyStatus === 'RESPONSE_SUBMITTED'
                      ? 'समीक्षा हेतु उत्तर प्रस्तुत किया जा चुका है।'
                      : 'खुली कमी (त्रुटि) पर उत्तर अपेक्षित है।'
                  }`
                : `${verifiedDocCount} of ${totalDocCount} scrutiny documents verified. ${
                    deficiencyStatus === 'RESPONSE_SUBMITTED'
                      ? 'A response has been submitted for review.'
                      : 'An open deficiency requires a response.'
                  }`}
            </p>
            <div className="buttonrow">
              <button className="btn" onClick={() => navigate('/documents')}>
                {isHi ? 'दस्तावेज़ तत्परता' : 'Document readiness'}
              </button>
              <button className="btn" onClick={() => navigate('/deficiencies')}>
                {isHi ? 'कमी सूचना खोलें' : 'Open deficiency'}
              </button>
            </div>
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>{isHi ? 'सशर्त समीक्षाएं' : 'Conditional reviews'}</h2>
            </div>
            <div className="listrow">
              <div>
                <strong>{isHi ? 'ईवीसी निरीक्षण' : 'EVC inspection'}</strong>
                <small>{isHi ? 'इस सांकेतिक प्रदर्शन मार्ग पर लागू' : 'Applicable to this synthetic demonstration route'}</small>
              </div>
              <button className="btn text" onClick={() => navigate('/evc')}>
                {isHi ? 'ईवीसी देखें →' : 'View EVC →'}
              </button>
            </div>
            <div className="listrow">
              <div>
                <strong>{isHi ? 'समिति समीक्षा' : 'Committee review'}</strong>
                <small>{isHi ? 'जब तक मामले हेतु विन्यासित न हो, लागू नहीं' : 'Not applicable unless configured for the case'}</small>
              </div>
              <span className="badge">{isHi ? 'सशर्त' : 'Conditional'}</span>
            </div>
          </section>
        </div>

        {/* Right Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>{isHi ? 'निर्णय इतिहास' : 'Decision history'}</h2>
            </div>
            <p className="muted">
              {isHi ? 'इस डेमो मामले हेतु कोई निर्णय दर्ज नहीं है।' : 'No decision recorded for this demo case.'}
            </p>
            <p className="notice">
              {isHi
                ? 'जहां औपचारिक अस्वीकृति दर्ज है परंतु कारण अनुपलब्ध है: "उपलब्ध डेटासेट में कारण उपलब्ध नहीं है।" कमी अस्वीकृति नहीं है।'
                : 'Where a formal rejection is recorded but reason is missing: "Reason not available in supplied dataset." A deficiency is distinct from rejection.'}
            </p>
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>{isHi ? 'हालिया गतिविधि' : 'Recent activity'}</h2>
            </div>
            <div className="timeline">
              {auditLogs.slice(0, 3).map((log) => (
                <div key={log.id} className="listrow">
                  <div>
                    <strong>{log.action}</strong>
                    <small>
                      {log.time} · {log.role}
                    </small>
                  </div>
                </div>
              ))}
              <div className="listrow">
                <div>
                  <strong>{isHi ? 'संवीक्षा निर्धारित' : 'Scrutiny scheduled'}</strong>
                  <small>{isHi ? 'सांकेतिक आधारभूत घटना · 28 अक्टूबर 2026' : 'Synthetic baseline event · 28 Oct 2026'}</small>
                </div>
              </div>
              <div className="listrow">
                <div>
                  <strong>{isHi ? 'आवेदन प्रस्तुत' : 'Application submitted'}</strong>
                  <small>{isHi ? 'सांकेतिक आधारभूत घटना · 20 अक्टूबर 2026' : 'Synthetic baseline event · 20 Oct 2026'}</small>
                </div>
              </div>
            </div>
            <button className="btn text" onClick={() => navigate('/audit')}>
              {isHi ? 'लेखा परीक्षा इतिहास देखें →' : 'View audit history →'}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
};
