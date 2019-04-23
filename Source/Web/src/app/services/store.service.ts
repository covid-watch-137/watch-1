import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { AppConfig } from '../app.config';
import { HttpService } from './http.service';
import { Store } from './store';

@Injectable()
export class StoreService {

  // Core
  public User = new Store(this.http, 'users');
  public RestAuthUser = new Store(this.http, 'user');
  public AddUser = new Store(this.http, 'add_user');
  public Organization = new Store(this.http, 'organizations');
  public Facility = new Store(this.http, 'facilities');
  public EmployeeProfile = new Store(this.http, 'employee_profiles');
  public ProviderTitle = new Store(this.http, 'provider_titles');
  public ProviderRole = new Store(this.http, 'provider_roles');
  public EmployeeRole = new Store(this.http, 'employee_roles');
  public ProviderSpecialty = new Store(this.http, 'provider_specialties');
  public Diagnosis = new Store(this.http, 'diagnosis');
  public Medication = new Store(this.http, 'medications');
  public Procedure = new Store(this.http, 'procedures');
  public Symptom = new Store(this.http, 'symptoms');
  // Billing
  public BilledActivity = new Store(this.http, 'billed_activities');
  public BillingCoordinator = new Store(this.http, 'billing_coordinators');
  public BillingType = new Store(this.http, 'billing_types');
  // Patients
  public PatientProfile = new Store(this.http, 'patient_profiles');
  public ProblemArea = new Store(this.http, 'problem_areas');
  public PatientDiagnosis = new Store(this.http, 'patient_diagnosis');
  public PatientProcedure = new Store(this.http, 'patient_procedures');
  public PatientMedication = new Store(this.http, 'patient_medications');
  public PotentialPatient = new Store(this.http, 'potential_patients');
  public PatientStat = new Store(this.http, 'patient_stats');
  // Plans
  public CarePlanTemplate = new Store(this.http, 'care_plan_templates');
  public CareTeamMember = new Store(this.http, 'care_team_members');
  public ServiceArea = new Store(this.http, 'service_areas');
  public CarePlan = new Store(this.http, 'care_plans');
  public PlanConsentForm = new Store(this.http, 'plan_consent_forms');
  public GoalTemplate = new Store(this.http, 'goal_templates');
  public Goal = new Store(this.http, 'goals');
  public GoalProgress = new Store(this.http, 'goal_progresses');
  public GoalComment = new Store(this.http, 'goal_comments');
  public InfoMessageQueue = new Store(this.http, 'info_message_queues');
  public InfoMessage = new Store(this.http, 'info_messages');
  // Tasks
  public PatientTaskTemplate = new Store(this.http, 'patient_task_templates');
  public PlanPatientTemplates = new Store(this.http, 'plan_patient_templates')
  public PatientTask = new Store(this.http, 'patient_tasks');
  public TeamTaskTemplate = new Store(this.http, 'team_task_templates');
  public TeamTask = new Store(this.http, 'team_tasks');
  public MedicationTaskTemplate = new Store(this.http, 'medication_task_templates');
  public MedicationTask = new Store(this.http, 'medication_tasks');
  public SymptomTaskTemplate = new Store(this.http, 'symptom_task_templates');
  public SymptomTask = new Store(this.http, 'symptom_tasks');
  public SymptomRating = new Store(this.http, 'symptom_ratings');
  public AssessmentTaskTemplate = new Store(this.http, 'assessment_task_templates');
  public AssessmentQuestion = new Store(this.http, 'assessment_questions');
  public AssessmentTask = new Store(this.http, 'assessment_tasks');
  public AssessmentResponse = new Store(this.http, 'assessment_responses');
  public VitalsTaskTemplate = new Store(this.http, 'vital_task_templates');
  public VitalsQuestions = new Store(this.http, 'vital_questions');
  public VitalResponse = new Store(this.http, 'vital_responses');

  constructor(private http: HttpService) { }
}
