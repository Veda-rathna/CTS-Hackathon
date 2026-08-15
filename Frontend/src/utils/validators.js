/**
 * Validation helpers for the nested Prior Authorization form data.
 */

export function validatePAForm(formData) {
  const errors = {};
  
  if (!formData || !formData.pa_requests || !formData.pa_requests[0]) {
    errors.general = 'Form data is missing or corrupted.';
    return { isValid: false, errors };
  }

  const pa = formData.pa_requests[0];
  const { patient, request, provider, service, diagnoses } = pa;

  // PA Request
  if (!pa.pa_request_id || !pa.pa_request_id.trim()) {
    errors.pa_request_id = 'PA Request ID is required (e.g. PA-001).';
  }

  // Patient validations
  if (!patient.patient_id || !patient.patient_id.trim()) {
    errors['patient.patient_id'] = 'Patient ID is required.';
  }
  if (!patient.date_of_birth) {
    errors['patient.date_of_birth'] = 'Date of Birth is required.';
  }
  if (patient.age === '' || patient.age === null || isNaN(Number(patient.age)) || Number(patient.age) < 0) {
    errors['patient.age'] = 'Age must be a valid positive number.';
  }
  if (!patient.gender) {
    errors['patient.gender'] = 'Gender is required.';
  }
  if (!patient.state || !patient.state.trim()) {
    errors['patient.state'] = 'Patient State is required.';
  }
  if (!patient.payer || !patient.payer.trim()) {
    errors['patient.payer'] = 'Payer is required.';
  }

  // Request validations
  if (!request.request_date) {
    errors['request.request_date'] = 'Request Date is required.';
  }
  if (!request.review_type) {
    errors['request.review_type'] = 'Review Type is required (e.g. NON_URGENT, URGENT).';
  }
  if (!request.request_type) {
    errors['request.request_type'] = 'Request Type is required (e.g. INITIAL, RENEWAL).';
  }

  // Provider validations
  if (!provider.provider_id || !provider.provider_id.trim()) {
    errors['provider.provider_id'] = 'Provider ID is required.';
  }
  if (!provider.specialty || !provider.specialty.trim()) {
    errors['provider.specialty'] = 'Provider Specialty is required.';
  }
  if (!provider.organization_id || !provider.organization_id.trim()) {
    errors['provider.organization_id'] = 'Organization ID is required.';
  }
  if (!provider.organization_name || !provider.organization_name.trim()) {
    errors['provider.organization_name'] = 'Organization Name is required.';
  }
  if (!provider.state || !provider.state.trim()) {
    errors['provider.state'] = 'Provider State is required.';
  }

  // Service validations
  if (!service.service_description || !service.service_description.trim()) {
    errors['service.service_description'] = 'Service Description is required.';
  }
  if (!service.procedure_code_system || !service.procedure_code_system.trim()) {
    errors['service.procedure_code_system'] = 'Procedure Code System is required.';
  }
  if (!service.start_date) {
    errors['service.start_date'] = 'Service Start Date is required.';
  }
  if (!service.end_date) {
    errors['service.end_date'] = 'Service End Date is required.';
  }
  if (service.start_date && service.end_date && service.start_date > service.end_date) {
    errors['service.end_date'] = 'End Date cannot be earlier than Start Date.';
  }
  if (service.number_of_sessions === '' || isNaN(Number(service.number_of_sessions)) || Number(service.number_of_sessions) < 1) {
    errors['service.number_of_sessions'] = 'Sessions must be at least 1.';
  }

  // Diagnoses validation
  if (!diagnoses || diagnoses.length === 0) {
    errors['diagnoses'] = 'At least one diagnosis entry is required.';
  } else {
    diagnoses.forEach((diag, index) => {
      if (!diag.description || !diag.description.trim()) {
        errors[`diagnoses.${index}.description`] = 'Diagnosis description is required.';
      }
      if (!diag.source_code || !diag.source_code.trim()) {
        errors[`diagnoses.${index}.source_code`] = 'Source code is required.';
      }
      if (!diag.source_code_system || !diag.source_code_system.trim()) {
        errors[`diagnoses.${index}.source_code_system`] = 'Code system is required.';
      }
    });
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}
