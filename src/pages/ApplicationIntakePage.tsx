import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  ArrowLeft,
  ShieldAlert,
  Send,
  Building2,
  Mail,
  Phone,
  User,
  Users,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { toast } from '../components/common/Toast';
import { ApplicationCategory } from '../types';

// Zod validation schema
const intakeSchema = z.object({
  name: z.string().min(4, 'Institution name must be at least 4 characters long'),
  city: z.string().min(3, 'City & State is required (e.g., Pune, Maharashtra)'),
  type: z.enum([
    'Extension of Approval',
    'Increase in Intake',
    'New Course',
    'New Institution',
  ] as const),
  applicantName: z.string().min(3, 'Contact applicant name is required'),
  contactEmail: z.string().email('Enter a valid institutional email address'),
  contactPhone: z
    .string()
    .min(10, 'Enter a valid phone number (min 10 digits)')
    .regex(/^[0-9+\s-]+$/, 'Phone number must contain only numbers, spaces, or dashes'),
  intakeCapacity: z
    .number({ invalid_type_error: 'Enter a valid student intake capacity' })
    .min(30, 'Minimum approved intake capacity is 30')
    .max(5000, 'Intake capacity cannot exceed 5000 in this cycle'),
  documentsUploaded: z
    .boolean()
    .refine((val) => val === true, 'You must acknowledge the statutory checklist requirement'),
});

type IntakeFormData = z.infer<typeof intakeSchema>;

import { apiClient } from '../api/client';

export const ApplicationIntakePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<IntakeFormData>({
    resolver: zodResolver(intakeSchema),
    defaultValues: {
      type: 'Extension of Approval',
      intakeCapacity: 360,
      documentsUploaded: false,
    },
  });

  const selectedType = watch('type');

  // Route calculation based on category (Illustrative demo routing)
  const getAssignedRoute = (type: ApplicationCategory): string => {
    switch (type) {
      case 'Extension of Approval':
        return 'Route A: Standard EoA (Illustrative)';
      case 'Increase in Intake':
        return 'Route B: Capacity Expansion (Illustrative)';
      case 'New Course':
        return 'Route C: Curriculum Addition (Illustrative)';
      case 'New Institution':
        return 'Route D: Green-field Establishment (Illustrative)';
      default:
        return 'Route A: Standard EoA';
    }
  };

  // Prevent accidental loss of unsaved edits
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  const onSubmit = async (data: IntakeFormData) => {
    try {
      const assignedRoute = getAssignedRoute(data.type);
      const now = new Date();
      // 21 days deadline from now
      const targetDeadline = new Date(now.getTime() + 21 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0];

      const newApp = await apiClient.createApplication({
        name: data.name,
        city: data.city,
        type: data.type,
        owner: 'Scrutiny desk',
        deadline: targetDeadline,
        deficiency: '',
        documents: ['Land ownership certificate', 'Faculty roster', 'Fire safety NOC'],
        assignedRoute,
        contactEmail: data.contactEmail,
        contactPhone: data.contactPhone,
        applicantRole: 'Principal / Institutional Representative',
        intakeCapacity: data.intakeCapacity,
        programsOffered: ['Engineering & Technology Programs'],
      });

      toast.show(
        `Application registered successfully! Assigned ID: ${newApp.id}`,
        'success'
      );

      navigate(`/applications/${newApp.id}`);
    } catch (err: any) {
      toast.show(err?.message || 'Failed to submit application to unified gateway', 'error');
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          if (!isDirty || window.confirm('Discard unsaved application intake data?')) {
            navigate('/applications');
          }
        }}
        icon={<ArrowLeft size={15} />}
        style={{ marginBottom: '16px' }}
      >
        Back to Applications
      </Button>

      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Institutional Self-Service</div>
          <h1 className="page-title">Application Intake Registration</h1>
          <p className="page-subtitle">
            Initiate a new approval cycle application. Technical input validation ensures completeness
            before desk scrutiny.
          </p>
        </div>
      </div>

      {/* Regulatory Scope Notice */}
      <div className="flow-callout" style={{ marginBottom: '22px' }}>
        <ShieldAlert size={20} color="var(--accent-active)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong>Illustrative Registration & Technical Validation</strong>
          <p>
            Form validation checks required fields and formats only. It does not constitute statutory
            scrutiny or confer approval status.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Institution & Application Particulars"
          subtitle="All fields marked with an asterisk (*) are mandatory for registration"
        />

        <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'grid', gap: '18px' }} noValidate>
          {/* Institution Name */}
          <div className="form-field">
            <label htmlFor="inst-name">
              Full Legal Name of Institution <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="inst-name"
                type="text"
                placeholder="e.g. Vidyanjali Institute of Technology"
                {...register('name')}
                style={{ paddingLeft: '34px' }}
              />
              <Building2
                size={16}
                color="var(--muted)"
                style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
              />
            </div>
            {errors.name && <p className="field-error">{errors.name.message}</p>}
          </div>

          {/* City and State */}
          <div className="form-field">
            <label htmlFor="inst-city">
              Campus Location (City, State) <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              id="inst-city"
              type="text"
              placeholder="e.g. Pune, Maharashtra"
              {...register('city')}
            />
            {errors.city && <p className="field-error">{errors.city.message}</p>}
          </div>

          {/* Category / Type */}
          <div className="form-field">
            <label htmlFor="inst-type">
              Application Category <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <select id="inst-type" {...register('type')}>
              <option value="Extension of Approval">Extension of Approval (EoA)</option>
              <option value="Increase in Intake">Increase in Intake</option>
              <option value="New Course">New Course Introduction</option>
              <option value="New Institution">Establishment of New Technical Institution</option>
            </select>
            {errors.type && <p className="field-error">{errors.type.message}</p>}
          </div>

          {/* Auto-assigned route banner */}
          <div
            style={{
              padding: '12px 14px',
              background: 'var(--surface-ivory)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--accent-border)',
              fontSize: '13px',
            }}
          >
            <span style={{ color: 'var(--muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700 }}>
              Calculated Approval Route
            </span>
            <div style={{ fontWeight: 700, color: 'var(--accent-active)', marginTop: '2px' }}>
              {getAssignedRoute(selectedType)}
            </div>
          </div>

          {/* Contact Person & Email Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-field">
              <label htmlFor="applicant-name">
                Authorized Signatory / Applicant Name <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="applicant-name"
                  type="text"
                  placeholder="e.g. Dr. K. Ramanathan"
                  {...register('applicantName')}
                  style={{ paddingLeft: '34px' }}
                />
                <User
                  size={16}
                  color="var(--muted)"
                  style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
                />
              </div>
              {errors.applicantName && (
                <p className="field-error">{errors.applicantName.message}</p>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="inst-capacity">
                Proposed Student Intake Capacity <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="inst-capacity"
                  type="number"
                  placeholder="e.g. 360"
                  {...register('intakeCapacity', { valueAsNumber: true })}
                  style={{ paddingLeft: '34px' }}
                />
                <Users
                  size={16}
                  color="var(--muted)"
                  style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
                />
              </div>
              {errors.intakeCapacity && (
                <p className="field-error">{errors.intakeCapacity.message}</p>
              )}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-field">
              <label htmlFor="inst-email">
                Institutional Email Address <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="inst-email"
                  type="email"
                  placeholder="aicte.office@institution.edu"
                  {...register('contactEmail')}
                  style={{ paddingLeft: '34px' }}
                />
                <Mail
                  size={16}
                  color="var(--muted)"
                  style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
                />
              </div>
              {errors.contactEmail && (
                <p className="field-error">{errors.contactEmail.message}</p>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="inst-phone">
                Official Contact Phone <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="inst-phone"
                  type="tel"
                  placeholder="+91 20 2567 8901"
                  {...register('contactPhone')}
                  style={{ paddingLeft: '34px' }}
                />
                <Phone
                  size={16}
                  color="var(--muted)"
                  style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
                />
              </div>
              {errors.contactPhone && (
                <p className="field-error">{errors.contactPhone.message}</p>
              )}
            </div>
          </div>

          {/* Confirmation Checkbox */}
          <div style={{ marginTop: '10px' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                cursor: 'pointer',
                fontSize: '13px',
                color: 'var(--fg-2)',
              }}
            >
              <input
                type="checkbox"
                {...register('documentsUploaded')}
                style={{ width: '18px', height: '18px', accentColor: 'var(--accent)', marginTop: 2 }}
              />
              <span>
                I confirm that land ownership certificates, approved faculty rosters, and current fire
                safety NOCs will be submitted for scrutiny under this application intake.
              </span>
            </label>
            {errors.documentsUploaded && (
              <p className="field-error" style={{ marginLeft: 28 }}>
                {errors.documentsUploaded.message}
              </p>
            )}
          </div>

          {/* Form Actions */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px',
              marginTop: '16px',
              paddingTop: '16px',
              borderTop: '1px solid var(--border-soft)',
            }}
          >
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                if (!isDirty || window.confirm('Discard unsaved application intake data?')) {
                  navigate('/applications');
                }
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              icon={<Send size={15} />}
            >
              Register & Submit for Scrutiny
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
