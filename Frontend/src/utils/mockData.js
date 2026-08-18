/**
 * Pre-seeded realistic Prior Authorization requests and evaluation cases.
 * Matching the exact JSON schema specification and backend response structures.
 */

export const INITIAL_PA_REQUESTS = [
  {
    pa_request_id: "PA-OPT-001",
    patient: {
      patient_id: "1f2982d5-e5da-6d4a-38d7-d7e7323880bb",
      date_of_birth: "1958-04-12",
      age: 68,
      gender: "F",
      state: "TX",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-18",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "PRV-ORTHO-01",
      specialty: "ORTHOPEDIC SURGERY",
      organization_id: "ORG-TX-01",
      organization_name: "AUSTIN ORTHOPEDIC INSTITUTE",
      state: "TX"
    },
    service: {
      service_description: "Intraarticular Knee Injections of Hyaluronan (Viscosupplementation)",
      procedure_code: "20610",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-18",
      end_date: "2026-08-18",
      place_of_service: "Outpatient Clinic",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Unilateral primary osteoarthritis, right knee",
        source_code: "M17.11",
        source_code_system: "ICD-10-CM",
        icd10_code: "M17.11",
        icd10_mapping_required: false
      }
    ],
    status: "COMPLETED",
    decision: "APPROVED",
    evidence_score: 0.96,
    requires_prior_authorization: true,
    reason: "The procedure and diagnosis match an active applicable policy (LCD L39529 / Article A56157).",
    decision_basis: "High-volume procedure 20610 with ICD-10 M17.11 satisfied conservative management and imaging criteria via fast-path cache.",
    policies: [
      {
        policy_type: "LCD",
        policy_id: "L39529",
        title: "Hyaluronan Acid Therapies for Knee Osteoarthritis",
        article_id: "A56157"
      }
    ],
    evidence: [
      {
        type: "HCPCS",
        identifier: "A56157",
        code: "20610",
        result: "MATCHED",
        explanation: "Procedure code 20610 is listed in Article A56157 covered CPT/HCPCS list."
      },
      {
        type: "ICD10",
        identifier: "A56157",
        code: "M17.11",
        result: "COVERED",
        explanation: "Diagnosis code M17.11 is covered under Article A56157."
      },
      {
        type: "JURISDICTION",
        identifier: "J5",
        state: "TX",
        result: "MATCHED",
        explanation: "State TX falls within Medicare Administrative Contractor Novitas Jurisdiction J5."
      }
    ],
    criteria: [
      {
        criterion_id: "CRIT-OPT-01",
        policy_type: "LCD",
        policy_id: "L39529",
        criterion: "Symptomatic primary osteoarthritis of the knee documented on exam and imaging.",
        criterion_type: "SEMANTIC",
        evaluator: "AGENTIC_QWEN",
        status: "SATISFIED",
        patient_evidence: ["Grade 3 joint space narrowing on plain radiographs."],
        policy_evidence: ["LCD L39529 Section 2 Clinical Indication"],
        mandatory: true,
        authoritative: false,
        explanation: "Documentation confirms symptomatic osteoarthritis with radiographic grading."
      },
      {
        criterion_id: "CRIT-OPT-02",
        policy_type: "LCD",
        policy_id: "L39529",
        criterion: "Failure of a trial of conservative therapy for at least 6 weeks.",
        criterion_type: "SEMANTIC",
        evaluator: "AGENTIC_QWEN",
        status: "SATISFIED",
        patient_evidence: ["Completed 12-week structured physical therapy and oral NSAIDs."],
        policy_evidence: ["LCD L39529 Conservative Management Protocol"],
        mandatory: true,
        authoritative: false,
        explanation: "Patient completed 12 weeks of supervised physical therapy, exceeding the 6-week minimum."
      }
    ],
    missing_information: [],
    warnings: []
  },
  {
    pa_request_id: "PA-001",
    patient: {
      patient_id: "p001",
      date_of_birth: "1971-04-12",
      age: 55,
      gender: "M",
      state: "TX",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-10",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "prov-tx-092",
      specialty: "INTERVENTIONAL PAIN MANAGEMENT",
      organization_id: "org-houston-01",
      organization_name: "TEXAS SPINE & PAIN SPECIALISTS",
      state: "TX"
    },
    service: {
      service_description: "Lumbar transforaminal epidural injection under fluoroscopic guidance for severe radiculopathy refractory to 8 weeks physical therapy.",
      procedure_code: "64483",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-20",
      end_date: "2026-08-20",
      place_of_service: "Ambulatory Surgical Center",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Lumbar radiculopathy, lumbosacral region",
        source_code: "M54.16",
        source_code_system: "ICD-10-CM",
        icd10_code: "M54.16",
        icd10_mapping_required: false
      }
    ],
    status: "COMPLETED",
    decision: "APPROVED",
    evidence_score: 0.95,
    requires_prior_authorization: true,
    reason: "The procedure and diagnosis match an active applicable policy (LCD L39054).",
    decision_basis: "Procedure 64483 and ICD-10 M54.16 satisfied all clinical coverage criteria in Novitas Jurisdiction J5. Evidence Fusion: COVERED.",
    policies: [
      {
        policy_type: "LCD",
        policy_id: "L39054",
        title: "Epidural Injections for Pain Management",
        article_id: "A12345"
      }
    ],
    evidence: [
      {
        type: "HCPCS",
        identifier: "A12345",
        code: "64483",
        result: "MATCHED",
        explanation: "Procedure code 64483 is listed in article A12345 covered CPT/HCPCS list."
      },
      {
        type: "ICD10",
        identifier: "A12345",
        code: "M54.16",
        result: "COVERED",
        explanation: "Diagnosis code M54.16 is in article A12345 covered ICD-10 table."
      },
      {
        type: "JURISDICTION",
        identifier: "J5",
        state: "TX",
        result: "MATCHED",
        explanation: "State TX falls within Medicare Administrative Contractor Novitas Jurisdiction J5."
      }
    ],
    criteria: [
      {
        criterion_id: "CRIT-001",
        policy_type: "LCD",
        policy_id: "L39054",
        criterion: "Radiculopathy confirmed on neuroimaging or electromyography.",
        criterion_type: "SEMANTIC",
        evaluator: "LLM",
        status: "SATISFIED",
        patient_evidence: ["MRI confirms L5-S1 nerve root compression"],
        policy_evidence: ["LCD L39054 Section 4.2 Imaging Criteria"],
        mandatory: true,
        authoritative: false,
        explanation: "Clinical notes document confirmed lumbar radiculopathy via imaging."
      },
      {
        criterion_id: "CRIT-002",
        policy_type: "LCD",
        policy_id: "L39054",
        criterion: "Failure of conservative therapy for at least 6 weeks.",
        criterion_type: "SEMANTIC",
        evaluator: "LLM",
        status: "SATISFIED",
        patient_evidence: ["8 weeks physical therapy and NSAIDs tried without lasting relief"],
        policy_evidence: ["LCD L39054 Conservative Therapy Prerequisite"],
        mandatory: true,
        authoritative: false,
        explanation: "Patient completed 8 weeks of physical therapy, exceeding the 6-week minimum."
      }
    ],
    missing_information: [],
    warnings: []
  },
  {
    pa_request_id: "PA-002",
    patient: {
      patient_id: "p002",
      date_of_birth: "1979-02-20",
      age: 47,
      gender: "M",
      state: "MA",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-01",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: true
    },
    provider: {
      provider_id: "prov018",
      specialty: "GENERAL PRACTICE",
      organization_id: "org018",
      organization_name: "FENWAY COMMUNITY HEALTH CENTER INC",
      state: "MA"
    },
    service: {
      service_description: "Gingivectomy or gingivoplasty, four or more contiguous teeth or tooth bounded spaces per quadrant",
      procedure_code: null,
      procedure_code_system: "CPT/HCPCS_MAPPING_REQUIRED",
      start_date: "2026-08-15",
      end_date: "2026-08-15",
      place_of_service: "Outpatient Dental Surgical Suite",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Gingival disease (disorder)",
        source_code: "18718003",
        source_code_system: "SNOMED-CT",
        icd10_code: null,
        icd10_mapping_required: true
      }
    ],
    status: "PENDING",
    decision: "ADDITIONAL_EVIDENCE_REQUIRED",
    evidence_score: 0.35,
    requires_prior_authorization: null,
    reason: "Procedure code and diagnosis codes require explicit CPT/HCPCS and ICD-10 mapping for policy matching.",
    decision_basis: "SNOMED code 18718003 requires crosswalk to ICD-10-CM. Procedure code is unassigned. Evidence Fusion: NOT_ADDRESSED.",
    policies: [],
    evidence: [
      {
        type: "HCPCS",
        identifier: null,
        code: null,
        result: "MISSING",
        explanation: "No standardized CPT/HCPCS procedure code supplied. Code mapping required."
      },
      {
        type: "ICD10",
        identifier: null,
        code: "18718003",
        result: "REVIEW",
        explanation: "SNOMED-CT code provided; ICD-10-CM equivalent required for Medicare crosswalk."
      }
    ],
    criteria: [],
    missing_information: [
      "Standardized CPT/HCPCS procedure code",
      "Standardized ICD-10-CM diagnosis code (e.g., K05.10 or K06.8)"
    ],
    warnings: ["Automatic code crosswalk recommended before resubmitting."]
  },
  {
    pa_request_id: "PA-003",
    patient: {
      patient_id: "p003",
      date_of_birth: "1960-11-05",
      age: 65,
      gender: "F",
      state: "IL",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-12",
      review_type: "URGENT",
      request_type: "INITIAL",
      urgency_reason: "Acute leukemia in second remission requiring urgent transplant scheduling.",
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "prov-uchicago-44",
      specialty: "HEMATOLOGY & ONCOLOGY",
      organization_id: "org-uchicago-med",
      organization_name: "UNIVERSITY OF CHICAGO MEDICAL CENTER",
      state: "IL"
    },
    service: {
      service_description: "Allogeneic hematopoietic stem cell transplantation (HSCT) for acute myeloid leukemia in complete remission.",
      procedure_code: "38240",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-25",
      end_date: "2026-08-25",
      place_of_service: "Inpatient Hospital",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Acute myeloid leukemia, not having achieved remission",
        source_code: "C92.00",
        source_code_system: "ICD-10-CM",
        icd10_code: "C92.00",
        icd10_mapping_required: false
      }
    ],
    status: "COMPLETED",
    decision: "APPROVED",
    evidence_score: 0.90,
    requires_prior_authorization: true,
    reason: "Service is nationally covered under NCD NCD-110.23 for acute myeloid leukemia.",
    decision_basis: "HCPCS 38240 matches covered national determination NCD 110.23 Stem Cell Transplantation. Evidence Fusion: COVERED.",
    policies: [
      {
        policy_type: "NCD",
        policy_id: "NCD-110.23",
        title: "Stem Cell Transplantation",
        article_id: null
      }
    ],
    evidence: [
      {
        type: "HCPCS",
        identifier: "NCD-110.23",
        code: "38240",
        result: "MATCHED",
        explanation: "HCPCS 38240 is listed as covered in national determination NCD-110.23."
      },
      {
        type: "JURISDICTION",
        identifier: "NATIONAL",
        state: "IL",
        result: "MATCHED",
        explanation: "National Coverage Determinations apply nationwide across all jurisdictions."
      }
    ],
    criteria: [
      {
        criterion_id: "NCD-CRIT-1",
        policy_type: "NCD",
        policy_id: "NCD-110.23",
        criterion: "Patient diagnosed with high-risk acute leukemia in remission or planned consolidation.",
        criterion_type: "STRUCTURED",
        evaluator: "SQL",
        status: "SATISFIED",
        patient_evidence: ["ICD-10 C92.00 verified"],
        policy_evidence: ["NCD 110.23 Coverage Guidelines for AML"],
        mandatory: true,
        authoritative: true,
        explanation: "Criteria met based on deterministic diagnosis mapping."
      }
    ],
    missing_information: [],
    warnings: []
  },
  {
    pa_request_id: "PA-004",
    patient: {
      patient_id: "p004",
      date_of_birth: "1988-06-14",
      age: 38,
      gender: "F",
      state: "CA",
      payer: "Medicare Advantage"
    },
    request: {
      request_date: "2026-08-14",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "prov-sf-101",
      specialty: "PHYSICAL MEDICINE & REHABILITATION",
      organization_id: "org-ucsf-02",
      organization_name: "UCSF HEALTH CENTER",
      state: "CA"
    },
    service: {
      service_description: "Application of surface neurostimulator (TENS) for acute post-surgical thoracic pain.",
      procedure_code: "64550",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-22",
      end_date: "2026-09-22",
      place_of_service: "Outpatient Clinic",
      number_of_sessions: 4,
      duration: "30 days",
      frequency: "Weekly"
    },
    diagnoses: [
      {
        description: "Acute pain due to trauma",
        source_code: "G89.11",
        source_code_system: "ICD-10-CM",
        icd10_code: "G89.11",
        icd10_mapping_required: false
      }
    ],
    status: "PENDING",
    decision: "PENDING_REVIEW",
    evidence_score: 0.60,
    requires_prior_authorization: null,
    reason: "Governed by NCD N123 (160.7.1) Transcutaneous Electrical Nerve Stimulation (TENS) for Acute Pain. Requires manual review of post-operative documentation.",
    decision_basis: "NCD N123 requires documented trial period and failure of standard post-operative analgesia. Evidence Fusion: UNKNOWN.",
    policies: [
      {
        policy_type: "NCD",
        policy_id: "N123",
        title: "TENS for Acute Post-Operative Pain",
        article_id: null
      }
    ],
    evidence: [
      {
        type: "HCPCS",
        identifier: "N123",
        code: "64550",
        result: "MATCHED",
        explanation: "Procedure 64550 matches NCD N123."
      }
    ],
    criteria: [
      {
        criterion_id: "TENS-01",
        policy_type: "NCD",
        policy_id: "N123",
        criterion: "TENS limited to 30 days post-surgery with physician oversight.",
        criterion_type: "RULE",
        evaluator: "RULE",
        status: "SATISFIED",
        patient_evidence: ["Duration specified as 30 days"],
        policy_evidence: ["NCD 160.7.1 Limitation Clause"],
        mandatory: true,
        authoritative: false,
        explanation: "Service window strictly adheres to 30-day limit."
      }
    ],
    missing_information: ["Operative report showing surgical date and indication"],
    warnings: ["Ensure postoperative physician notes are submitted within 5 business days."]
  },
  {
    pa_request_id: "PA-005",
    patient: {
      patient_id: "p005",
      date_of_birth: "1965-03-12",
      age: 61,
      gender: "M",
      state: "TX",
      payer: "Medicare Part B"
    },
    request: {
      request_date: "2026-08-16",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "prov-tx-551",
      specialty: "PHYSICAL MEDICINE & REHABILITATION",
      organization_id: "org-houston-03",
      organization_name: "LONE STAR PAIN & SPINE CLINIC",
      state: "TX"
    },
    service: {
      service_description: "Acupuncture, 1 or more needles; initial 15 minutes for acute cervical neck pain following athletic injury.",
      procedure_code: "20552",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-25",
      end_date: "2026-08-25",
      place_of_service: "Outpatient Clinic",
      number_of_sessions: 5,
      duration: "30 days",
      frequency: "Weekly"
    },
    diagnoses: [
      {
        description: "Cervicalgia (acute neck pain)",
        source_code: "M54.2",
        source_code_system: "ICD-10-CM",
        icd10_code: "M54.2",
        icd10_mapping_required: false
      }
    ],
    status: "COMPLETED",
    decision: "REJECTED",
    evidence_score: 0.10,
    requires_prior_authorization: true,
    reason: "Acupuncture for indications other than Chronic Low Back Pain (cLBP) is explicitly excluded from Medicare coverage under NCD 373.",
    decision_basis: "NCD 373 limits acupuncture coverage strictly to Chronic Lower Back Pain lasting >12 weeks. Acute cervicalgia (M54.2) is a non-covered indication. Evidence Fusion: EXCLUDED.",
    policies: [
      {
        policy_type: "NCD",
        policy_id: "NCD 373",
        title: "Acupuncture for Chronic Lower Back Pain (cLBP)",
        article_id: null
      }
    ],
    evidence: [
      {
        type: "HCPCS",
        identifier: "NCD 373",
        code: "20552",
        result: "MATCHED",
        explanation: "Procedure 20552 evaluated against NCD 373 National Coverage Determination."
      },
      {
        type: "ICD10",
        identifier: "NCD 373",
        code: "M54.2",
        result: "NON_COVERED",
        explanation: "Diagnosis M54.2 (Cervicalgia) is not an approved indication under NCD 373."
      }
    ],
    criteria: [
      {
        criterion_id: "NCD-373-INDICATION",
        policy_type: "NCD",
        policy_id: "NCD 373",
        criterion: "Patient must have documented chronic lower back pain lasting >= 12 weeks.",
        criterion_type: "SEMANTIC",
        evaluator: "AGENTIC_QWEN",
        status: "NOT_SATISFIED",
        patient_evidence: ["Patient presents with acute neck pain (cervicalgia M54.2) following acute sports injury."],
        policy_evidence: ["NCD 373 Section 1: Covered Indications"],
        mandatory: true,
        authoritative: true,
        explanation: "The requested indication (acute neck pain) conflicts directly with the mandatory chronic lower back pain indication."
      }
    ],
    missing_information: [],
    warnings: ["Acupuncture for cervical/neck pain is non-covered nationwide under CMS policy."]
  }
];

export const SAMPLE_TEMPLATES = {
  epidural: {
    pa_request_id: "PA-SAMPLE-01",
    patient: {
      patient_id: "PT-88021",
      date_of_birth: "1968-05-14",
      age: 58,
      gender: "M",
      state: "TX",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-15",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "PR-99201",
      specialty: "PAIN MEDICINE",
      organization_id: "ORG-4421",
      organization_name: "AUSTIN REGIONAL PAIN CLINIC",
      state: "TX"
    },
    service: {
      service_description: "Lumbar transforaminal epidural steroid injection at L4-L5 level under imaging guidance. Patient has documented persistent radicular pain unrelieved by conservative management.",
      procedure_code: "64483",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-25",
      end_date: "2026-08-25",
      place_of_service: "Outpatient Surgical Suite",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Radiculopathy, lumbar region",
        source_code: "M54.16",
        source_code_system: "ICD-10-CM",
        icd10_code: "M54.16",
        icd10_mapping_required: false
      }
    ]
  },
  stemCell: {
    pa_request_id: "PA-SAMPLE-02",
    patient: {
      patient_id: "PT-55102",
      date_of_birth: "1961-09-22",
      age: 64,
      gender: "F",
      state: "IL",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-15",
      review_type: "URGENT",
      request_type: "INITIAL",
      urgency_reason: "High risk hematologic malignancy requiring immediate donor engraftment protocol.",
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "PR-33108",
      specialty: "HEMATOLOGY/ONCOLOGY",
      organization_id: "ORG-8822",
      organization_name: "NORTHWESTERN MEMORIAL HOSPITAL",
      state: "IL"
    },
    service: {
      service_description: "Allogeneic hematopoietic cell transplantation (HCT) from HLA-matched unrelated donor.",
      procedure_code: "38240",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-09-01",
      end_date: "2026-09-01",
      place_of_service: "Inpatient Hospital Bone Marrow Unit",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Acute myeloid leukemia without mention of remission",
        source_code: "C92.00",
        source_code_system: "ICD-10-CM",
        icd10_code: "C92.00",
        icd10_mapping_required: false
      }
    ]
  },
  dental: {
    pa_request_id: "PA-SAMPLE-03",
    patient: {
      patient_id: "PT-10992",
      date_of_birth: "1979-02-20",
      age: 47,
      gender: "M",
      state: "MA",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-15",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: true
    },
    provider: {
      provider_id: "PR-01822",
      specialty: "ORAL & MAXILLOFACIAL SURGERY",
      organization_id: "ORG-018",
      organization_name: "FENWAY COMMUNITY HEALTH CENTER INC",
      state: "MA"
    },
    service: {
      service_description: "Gingivectomy or gingivoplasty, four or more contiguous teeth or tooth bounded spaces per quadrant",
      procedure_code: null,
      procedure_code_system: "CPT/HCPCS_MAPPING_REQUIRED",
      start_date: "2026-08-30",
      end_date: "2026-08-30",
      place_of_service: "Outpatient Dental Surgical Suite",
      number_of_sessions: 1,
      duration: "1 day",
      frequency: "Once"
    },
    diagnoses: [
      {
        description: "Gingival disease (disorder)",
        source_code: "18718003",
        source_code_system: "SNOMED-CT",
        icd10_code: null,
        icd10_mapping_required: true
      }
    ]
  },
  acupunctureRejected: {
    pa_request_id: "PA-SAMPLE-04",
    patient: {
      patient_id: "PT-77201",
      date_of_birth: "1965-03-12",
      age: 61,
      gender: "M",
      state: "TX",
      payer: "Medicare"
    },
    request: {
      request_date: "2026-08-16",
      review_type: "NON_URGENT",
      request_type: "INITIAL",
      urgency_reason: null,
      previous_authorization_number: null,
      mock_request_field: false
    },
    provider: {
      provider_id: "PR-55109",
      specialty: "PHYSICAL MEDICINE & REHABILITATION",
      organization_id: "ORG-551",
      organization_name: "LONE STAR PAIN & SPINE CLINIC",
      state: "TX"
    },
    service: {
      service_description: "Acupuncture, 1 or more needles; initial 15 minutes for acute cervical neck pain (cervicalgia) following sports injury.",
      procedure_code: "20552",
      procedure_code_system: "HCPCS/CPT",
      start_date: "2026-08-25",
      end_date: "2026-08-25",
      place_of_service: "Outpatient Clinic",
      number_of_sessions: 5,
      duration: "30 days",
      frequency: "Weekly"
    },
    diagnoses: [
      {
        description: "Cervicalgia (acute neck pain)",
        source_code: "M54.2",
        source_code_system: "ICD-10-CM",
        icd10_code: "M54.2",
        icd10_mapping_required: false
      }
    ]
  }
};
