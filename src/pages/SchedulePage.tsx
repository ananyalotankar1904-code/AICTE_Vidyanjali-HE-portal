import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal, ROLES } from '../context/PortalContext';

export const SchedulePage: React.FC<{ officerMode?: boolean }> = ({ officerMode = false }) => {
  const navigate = useNavigate();
  const {
    role,
    appId,
    slotRescheduled,
    rescheduleRequested,
    submitRescheduleRequest,
    assignScrutinySlot,
    openDialog,
    showToast,
  } = usePortal();

  const isOfficer = officerMode || role !== ROLES[0];

  // Calendar month state
  const [calendarYear, setCalendarYear] = useState<number>(2026);
  const [calendarMonth, setCalendarMonth] = useState<number>(10); // 0-indexed: 10 = November

  const moveCalendar = (delta: number) => {
    const d = new Date(calendarYear, calendarMonth + delta, 1);
    setCalendarYear(d.getFullYear());
    setCalendarMonth(d.getMonth());
  };

  // Events list matching sih_final.html
  const events = [
    {
      year: 2026,
      month: 9, // October
      day: 20,
      title: 'Application submitted',
      detail: 'Synthetic baseline event',
      route: '/case',
    },
    {
      year: 2026,
      month: 9, // October
      day: 28,
      title: 'Scrutiny scheduled',
      detail: 'Synthetic baseline event',
      route: '/case',
    },
    {
      year: 2026,
      month: 10, // November
      day: slotRescheduled ? 6 : 5,
      title: 'Scrutiny meeting',
      detail: `11:00 AM IST · ${slotRescheduled ? 'Rescheduled' : 'Confirmed'}`,
      route: 'meeting-details',
    },
    {
      year: 2026,
      month: 10, // November
      day: 12,
      title: 'Response deadline',
      detail: 'Deficiency response due',
      route: '/deficiencies',
    },
  ];

  const monthEvents = events.filter(
    (e) => e.year === calendarYear && e.month === calendarMonth
  );

  const firstDayIndex = new Date(calendarYear, calendarMonth, 1).getDay();
  const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
  const monthName = new Date(calendarYear, calendarMonth, 1).toLocaleDateString('en-IN', {
    month: 'long',
    year: 'numeric',
  });

  const handleRequestSlot = () => {
    let reasonVal = '';
    let preferredVal = '';

    openDialog({
      title: 'Request a different slot',
      children: (
        <div>
          <p>The original appointment remains confirmed until a replacement is confirmed.</p>
          <label htmlFor="reschedule-reason">Reason</label>
          <textarea
            id="reschedule-reason"
            placeholder="Describe why another time is needed"
            onChange={(e) => {
              reasonVal = e.target.value;
            }}
          />
          <label htmlFor="reschedule-preferred">Preferred date and time</label>
          <input
            id="reschedule-preferred"
            type="datetime-local"
            onChange={(e) => {
              preferredVal = e.target.value;
            }}
          />
        </div>
      ),
      confirmLabel: 'Submit mock request',
      notice: 'This action changes local demo state only.',
      onConfirm: () => {
        if (!reasonVal || !preferredVal) {
          showToast('Add a reason and preferred time.');
          return;
        }
        submitRescheduleRequest(reasonVal, preferredVal);
      },
    });
  };

  const handleAssignSlot = () => {
    let selectedSlot = 'booked';
    let duration = '45 minutes';

    openDialog({
      title: 'Assign scrutiny slot',
      children: (
        <div>
          <p>Choose a slot for {appId}. The 05 November 11:00 slot is already booked.</p>
          <label htmlFor="slot-select">Available slot</label>
          <select
            id="slot-select"
            defaultValue="booked"
            onChange={(e) => {
              selectedSlot = e.target.value;
            }}
          >
            <option value="booked">05 Nov 2026 · 11:00 AM — booked</option>
            <option value="available">06 Nov 2026 · 11:00 AM — available</option>
          </select>
          <label htmlFor="duration-select">Duration</label>
          <select
            id="duration-select"
            defaultValue="45 minutes"
            onChange={(e) => {
              duration = e.target.value;
            }}
          >
            <option>45 minutes</option>
            <option>30 minutes</option>
            <option>60 minutes</option>
          </select>
        </div>
      ),
      confirmLabel: 'Assign demo slot',
      notice: 'This action changes local demo state only.',
      onConfirm: () => {
        assignScrutinySlot(selectedSlot as any, duration);
      },
    });
  };

  const renderEvent = () => (
    <div className="event">
      <div className="datebox">
        <small>NOV</small>
        <b>{slotRescheduled ? '06' : '05'}</b>
      </div>
      <div>
        <strong>Online scrutiny meeting</strong>
        <p>
          {slotRescheduled ? '06' : '05'} November 2026 · 11:00 AM IST · 45 min
        </p>
        <span className="badge blue">
          {slotRescheduled ? 'Rescheduled' : 'Confirmed'}
        </span>{' '}
        <p>Joining link: Not available in supplied dataset.</p>
      </div>
    </div>
  );

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>{isOfficer ? 'Scrutiny scheduling' : 'My schedule'}</h1>
          <p>
            {isOfficer
              ? 'Manage scrutiny appointments and review reschedule requests.'
              : 'Your confirmed events and preparation details.'}
          </p>
        </div>
        {isOfficer ? (
          <button className="btn primary" onClick={handleAssignSlot}>
            Assign a slot
          </button>
        ) : (
          <button className="btn" onClick={handleRequestSlot}>
            Request a different slot
          </button>
        )}
      </div>

      {/* Interactive Monthly Calendar (Available to both applicant and officer) */}
      <section className="card" style={{ marginBottom: '16px' }}>
        <div className="cardhead">
          <div>
            <h2>Application calendar</h2>
            <p>Select any marked date to inspect scheduled hearings and statutory deadlines.</p>
          </div>
        </div>

        <div className="calendar-toolbar">
          <div>
            <h3>{monthName}</h3>
            <span className="notice">Select a marked date to view its event</span>
          </div>
          <div className="calendar-controls">
            <button
              className="iconbtn"
              aria-label="Previous month"
              onClick={() => moveCalendar(-1)}
            >
              ‹
            </button>
            <button
              className="iconbtn"
              aria-label="Next month"
              onClick={() => moveCalendar(1)}
            >
              ›
            </button>
          </div>
        </div>

        <div className="calendar-grid" aria-label={`Calendar for ${monthName}`}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d} className="calendar-weekday">
              {d}
            </div>
          ))}

          {/* Blank offset cells */}
          {Array.from({ length: firstDayIndex }).map((_, i) => (
            <div key={`blank-${i}`} className="calendar-day blank" aria-hidden="true" />
          ))}

          {/* Month day cells */}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const dayNum = i + 1;
            const dayItems = monthEvents.filter((e) => e.day === dayNum);
            if (dayItems.length > 0) {
              return (
                <button
                  key={`day-${dayNum}`}
                  className="calendar-day has-event"
                  aria-label={`${dayNum} ${monthName}: ${dayItems
                    .map((e) => e.title)
                    .join(', ')}`}
                  onClick={() => {
                    const el = document.getElementById(`calendar-item-${dayNum}`);
                    if (el) {
                      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      el.focus();
                    }
                  }}
                >
                  <strong>{dayNum}</strong>
                  <small>{dayItems.map((e) => e.title).join(', ')}</small>
                </button>
              );
            }
            return (
              <div key={`day-${dayNum}`} className="calendar-day">
                <strong>{dayNum}</strong>
              </div>
            );
          })}
        </div>

        <div className="calendar-legend">
          <span>Event or deadline</span>
          <span>All times shown in IST</span>
        </div>

        <div className="calendar-agenda">
          <h3>Timeline · {monthName}</h3>
          {monthEvents.length > 0 ? (
            monthEvents.map((e) => (
              <div
                key={e.day}
                className="listrow"
                id={`calendar-item-${e.day}`}
                tabIndex={-1}
              >
                <div>
                  <strong>
                    {e.day} {monthName} · {e.title}
                  </strong>
                  <small>{e.detail}</small>
                </div>
                {e.route === 'meeting-details' ? (
                  <a href="#meeting-details" className="btn text">
                    View meeting →
                  </a>
                ) : (
                  <button className="btn text" onClick={() => navigate(e.route)}>
                    Open →
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="muted">No events or deadlines in this month.</p>
          )}
        </div>
      </section>

      {/* Columns */}
      <div className="grid columns">
        {/* Left Stack */}
        <div className="stack">
          <div id="meeting-details">
            <section className="card">
              <div className="cardhead">
                <h2>Upcoming scrutiny meeting</h2>
              </div>
              {renderEvent()}
              <hr className="divider" />
              <p>
                <strong>Required representatives:</strong> Principal and authorised representative
              </p>
              <p>
                <strong>Preparation:</strong> Bring identification and the management authorisation letter.
              </p>
              {rescheduleRequested && (
                <span className="badge amber">Reschedule Requested</span>
              )}
            </section>
          </div>

          <section className="card">
            <div className="cardhead">
              <h2>Meeting outcome &amp; follow-up</h2>
            </div>
            <p className="muted">
              No outcome recorded. Follow-up tasks will appear after the meeting.
            </p>
          </section>
        </div>

        {/* Right Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>{isOfficer ? 'Scheduling queue' : 'Reschedule requests'}</h2>
            </div>
            {rescheduleRequested ? (
              <div>
                <p>
                  Request awaiting officer review. The original appointment remains confirmed.
                </p>
                {isOfficer ? (
                  <button className="btn primary" onClick={handleAssignSlot}>
                    Review and assign slot
                  </button>
                ) : (
                  <span className="badge amber">Awaiting review</span>
                )}
              </div>
            ) : (
              <p className="muted">No open reschedule requests.</p>
            )}
          </section>

          <section className="card">
            <div className="cardhead">
              <h2>Availability</h2>
            </div>
            <div className="listrow">
              <strong>05 Nov · 11:00 AM</strong>
              <span className="badge red">Booked</span>
            </div>
            <div className="listrow">
              <strong>06 Nov · 11:00 AM</strong>
              <span className="badge green">Available</span>
            </div>
            <div className="listrow">
              <strong>06 Nov · 2:00 PM</strong>
              <span className="badge">Blocked</span>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

