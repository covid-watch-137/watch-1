import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ModalService, ConfirmModalComponent } from '../../../modules/modals';
import {
  AddAssessmentComponent,
  AddCTTaskComponent,
  AddStreamComponent,
  AddVitalComponent,
  CreateAssessmentComponent,
  CreateStreamComponent,
  EditTaskComponent,
  GoalComponent,
  PreviewVitalComponent,
  CreateVitalComponent,
  PlanDurationComponent,
} from '../../../components';
import { NavbarService, StoreService } from '../../../services';

@Component({
  selector: 'app-plan-schedule',
  templateUrl: './schedule.component.html',
  styleUrls: ['./schedule.component.scss'],
})
export class PlanScheduleComponent implements OnDestroy, OnInit {

  public planTemplateId = null;
  public planTemplate = null;
  public goalTemplates = [];
  public teamTaskTemplates = [];
  public teamManagerTemplates = [];
  public teamMemberTemplates = [];
  public patientTaskTemplates = [];
  public symptomTemplates = [];
  public assessmentTemplates = [];
  public vitalTemplates = [];
  public messageQueues = [];

  public accordionsOpen = [];
  public tooltipsOpen = [];

  constructor(
    private route: ActivatedRoute,
    private modals: ModalService,
    private nav: NavbarService,
    private store: StoreService,
  ) { }

  public ngOnInit() {
    this.route.params.subscribe((params) => {
      this.planTemplateId = params.id;
      this.nav.planDetailState(this.planTemplateId);
      this.store.CarePlanTemplate.read(this.planTemplateId).subscribe((planTemplate) => {
        this.planTemplate = planTemplate;
      });
      this.store.GoalTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((goals) => {
        this.goalTemplates = goals;
      });
      this.store.TeamTaskTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((teamTaskTemplates) => {
        this.teamTaskTemplates = teamTaskTemplates;
        this.teamManagerTemplates = teamTaskTemplates.filter((task) => task.is_manager_task);
        this.teamMemberTemplates = teamTaskTemplates.filter((task) => !task.is_manager_task);
      });
      this.store.SymptomTaskTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((symptoms) => {
        this.symptomTemplates = symptoms;
      });
      this.store.InfoMessageQueue.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((messages) => {
        this.messageQueues = messages;
      });
      this.store.VitalsTaskTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((vitals) => {
        this.vitalTemplates = vitals;
      });
      this.store.PatientTaskTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
        start_on_day: 1,
      }).subscribe((patientTasks) => {
        this.patientTaskTemplates = patientTasks;
      });
      this.store.AssessmentTaskTemplate.readListPaged({
        plan_template__id: this.planTemplateId,
      }).subscribe((assessments) => {
        this.assessmentTemplates = assessments;
      });
    });
  }

  public ngOnDestroy() { }

  public patientTasksCount() {
    return this.symptomTemplates.length + this.vitalTemplates.length + this.patientTaskTemplates.length + this.assessmentTemplates.length;
  }

  public formatStartOnDay(day) {
    if (day === 0) {
      return 'Plan Start';
    } else if (day >= 7) {
      return `Week ${day/7}`;
    } else {
      return `Day ${day}`;
    }
  }

  public formatEndOnDay(day, duration) {
    if (duration === -1) {
      return 'Until Plan Ends';
    } else {
      return `Week ${Math.round((day/7) + duration)}`;
    }
  }

  public openGoal() {
    let modalSub = this.modals.open(GoalComponent, {
      closeDisabled: true,
      data: {
        creatingTemplate: true,
      },
      width: '512px',
    }).subscribe(
      (results) => {
        if (results !== null) {
          let createSub = this.store.GoalTemplate.create({
            name: results.name,
            plan_template: this.planTemplateId,
            description: results.description,
            focus: results.focus,
            duration_weeks: results.duration_weeks,
            start_on_day: results.start_on_day,
          }).subscribe(
            (goal) => {
              this.goalTemplates.push(goal);
            },
            (err) => {},
            () => {
              createSub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public editGoal(goal) {
    let goalIndex = this.goalTemplates.findIndex((obj) => {
      return obj.id === goal.id;
    });
    let modalSub = this.modals.open(GoalComponent, {
      closeDisabled: true,
      data: {
        creatingTemplate: false,
        goalTemplate: goal,
      },
      width: '512px',
    }).subscribe(
      (results) => {
        if (results !== null) {
          let updateSub = this.store.GoalTemplate.update(goal.id, {
            name: results.name,
            description: results.description,
            focus: results.focus,
            duration_weeks: results.duration_weeks,
            start_on_day: results.start_on_day,
          }, true).subscribe(
            (updatedGoal) => {
              this.goalTemplates[goalIndex] = updatedGoal;
            },
            (err) => {},
            () => {
              updateSub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public confirmDeleteGoal(goal) {
    let goalIndex = this.goalTemplates.findIndex((obj) => {
      return obj.id === goal.id;
    });
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Goal?',
       body: `Are you sure you want to delete this care plan goal? This will affect X patients currently assigned to this care plan.`,
       cancelText: 'Cancel',
       okText: 'Confirm',
      },
      width: '384px',
    }).subscribe(
      (result) => {
        if (result.toLowerCase() === 'confirm') {
          let deleteSub = this.store.GoalTemplate.destroy(goal.id).subscribe(
            (data) => {
              this.goalTemplates.splice(goalIndex, 1);
            },
            (err) => {},
            () => {
              deleteSub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addCMTask() {
    let modalSub = this.modals.open(AddCTTaskComponent, {
      closeDisabled: true,
      width: '384px',
      data: {
        type: 'manager',
        planTemplateId: this.planTemplateId,
        taskList:this.teamManagerTemplates,
      },
    }).subscribe(
      (task) => {
        if (!task) {
          return;
        }
        this.editCMTask(task);
      },
      () => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public editCMTask(task) {
    let modalSub = this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      width: '384px',
      data: {
        task: task,
        type: 'manager',
      },
    }).subscribe(
      (task) => {},
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addCTTask() {
    let modalSub = this.modals.open(AddCTTaskComponent, {
      closeDisabled: true,
      width: '384px',
      data: {
        type: 'team',
        planTemplateId: this.planTemplateId,
        taskList:this.teamMemberTemplates,
      },
    }).subscribe(
      (task) => {
        if (task !== null) {
          this.editCTTask(task);
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public editCTTask(task) {
    let modalSub = this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      width: '384px',
      data: {
        task: task,
        type: 'team',
      },
    }).subscribe(
      (task) => {},
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public confirmDeleteCTTask(task, is_manager_task) {
    let tasksIndex = this.teamTaskTemplates.findIndex((obj) => {
      return obj.id === task.id;
    });
    let otherIndex = -1;
    if (is_manager_task) {
      otherIndex = this.teamManagerTemplates.findIndex((obj) => {
        return obj.id === task.id;
      });
    } else {
      otherIndex = this.teamMemberTemplates.findIndex((obj) => {
        return obj.id === task.id;
      });
    }
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Task?',
       body: 'Are you sure you want to remove this task? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'confirm',
      },
      width: '384px',
    }).subscribe(
      (data) => {
        if (data.toLowerCase() === 'confirm') {
          let destroySub = this.store.TeamTaskTemplate.destroy(task.id).subscribe(
            (resp) => {
              this.teamTaskTemplates.splice(tasksIndex, 1);
              if (is_manager_task) {
                this.teamManagerTemplates.splice(otherIndex, 1);
              } else {
                this.teamMemberTemplates.splice(otherIndex, 1);
              }
            },
            (err) => {},
            () => {
              destroySub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addTask() {
    let modalSub = this.modals.open(AddCTTaskComponent, {
      closeDisabled: true,
      data: {
        type: 'patient',
        planTemplateId: this.planTemplateId,
        taskList: this.patientTaskTemplates,
      },
      width: '384px',
    }).subscribe(
      (task) => {
        if (!task) {
          return;
        }
        this.editTask(task);
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public editTask(task) {
    let modalSub = this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      data: {
        task: task,
        type: 'patient',
      },
      width: '384px',
    }).subscribe(
      (task) => {},
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public confirmDeleteTask(task) {
    let tasksIndex = this.patientTaskTemplates.findIndex((obj) => {
      return obj.id === task.id;
    });
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Task?',
       body: 'Are you sure you want to remove this task? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'confirm',
      },
      width: '384px',
    }).subscribe(
      (resp) => {
        if (resp.toLowerCase() === 'confirm') {
          let deleteSub = this.store.PatientTaskTemplate.destroy(task.id).subscribe(
            (data) => {
              this.patientTaskTemplates.splice(tasksIndex, 1);
            },
            (err) => {},
            () => {
              deleteSub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addAssessment() {
    this.modals.open(AddAssessmentComponent, {
      closeDisabled: true,
      data: {
        editingTemplate: true,
        assessmentsList: this.assessmentTemplates,
        planTemplateId: this.planTemplateId,
      },
      width: '768px',
    }).subscribe((res) => {
      if (!res) {
        return;
      }
      if (res === 'create-new') {
        this.editAssessment(null);
      } else {
        this.editAssessment(res);
      }
    });
  }

  public editAssessment(assessment) {
    this.modals.open(CreateAssessmentComponent, {
      closeDisabled: true,
      data: {
        assessment: assessment,
        planTemplateId: this.planTemplateId,
      },
      width: '864px',
    }).subscribe((res) => {
      if (!res) {
        return;
      }
      let index = this.assessmentTemplates.findIndex((obj) => {
        return obj.id === assessment.id;
      });
      if (index >= 0) {
        this.assessmentTemplates[index] = res;
      } else {
        this.assessmentTemplates.push(res);
      }
    });
  }

  public editAssessmentTime(assessment) {
    this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      data: {
        task: assessment,
        type: 'assessment',
      },
      width: '384px'
    }).subscribe();
  }

  public confirmDeleteAssessment(assessment) {
    let tasksIndex = this.assessmentTemplates.findIndex((obj) => {
      return obj.id === assessment.id;
    });
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Assessment?',
       body: 'Are you sure you want to remove this assessment? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'Confirm',
      },
      width: '384px',
    }).subscribe(
      (data) => {
        if (data.toLowerCase() === 'confirm') {
          let destroySub = this.store.AssessmentTaskTemplate.destroy(assessment.id).subscribe(
            (data) => {
              this.assessmentTemplates.splice(tasksIndex, 1);
            },
            (err) => {},
            () => {
              destroySub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addSymptom() {
    this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      data: {
        type: 'symptom',
        task: {
          start_on_day: 0,
          appear_time: '00:00:00',
          due_time: '00:00:00',
          plan_template: this.planTemplateId,
          frequency: 'once',
        }
      },
      width: '384px',
    }).subscribe((symptom) => {
      if (!symptom) {
        return;
      }
      this.symptomTemplates.push(symptom);
    });
  }

  public editSymptom(symptom) {
    this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      data: {
        type: 'symptom',
        task: symptom,
      },
      width: '384px',
    }).subscribe(() => {});
  }

  public confirmDeleteSymptom(symptom) {
    let tasksIndex = this.symptomTemplates.findIndex((obj) => {
      return obj.id === symptom.id;
    });
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Symptom Report?',
       body: 'Are you sure you want to remove this symptom report? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'Confirm',
      },
      width: '384px',
    }).subscribe(
      (data) => {
        if (data.toLowerCase() === 'confirm') {
          let destroySub = this.store.SymptomTaskTemplate.destroy(symptom.id).subscribe(
            (data) => {
              this.symptomTemplates.splice(tasksIndex, 1);
            },
            (err) => {},
            () => {
              destroySub.unsubscribe();
            }
          );
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addVital(vitalTemplates) {
    this.modals.open(AddVitalComponent, {
      closeDisabled: true,
      width: '768px',
      data: {
        taskList: vitalTemplates,
        planTemplateId: this.planTemplateId,
      },
    }).subscribe((data) => {
      if (!data || !data.nextAction) {
        return;
      }
      switch(data.nextAction)
      {
        case 'fullVitalPreview':
            this.previewVital(data.data);
            break;
        case 'editVital':
            this.editVital(data.data);
            break;
        default:
             break;
      }
    });
  }

  public editVital(vital) {
    this.modals.open(CreateVitalComponent, {
      closeDisabled: true,
      width: '800px',
      data: {
        vital: vital,
        planTemplateId: this.planTemplateId,
      }
    }).subscribe((res) => {
      if (!res) {
        return;
      }
      let index = this.vitalTemplates.findIndex((obj) => {
        return obj.id === vital.id;
      });
      if (index >= 0) {
        this.vitalTemplates[index] = res;
      } else {
        this.vitalTemplates.push(res);
      }
    });
  }

  public editVitalTime(vital) {
    let modalSub = this.modals.open(EditTaskComponent, {
      closeDisabled: true,
      data: {
        type: 'vital',
        task: vital,
      },
      width: '384px',
    }).subscribe(
      (data) => {},
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public previewVital(vital) {
    this.modals.open(PreviewVitalComponent, {
      closeDisabled: true,
      width: '500px',
      data: vital
    }).subscribe(() => {});
  }

  public confirmDeleteVital(vital) {
    let tasksIndex = this.vitalTemplates.findIndex((obj) => {
      return obj.id === vital.id;
    });
    let modalSub = this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Vital?',
       body: 'Are you sure you want to remove this vital report? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'Confirm',
      },
      width: '384px',
    }).subscribe(
      (data) => {
        if (!data) {
          return;
        }
        if (data.toLowerCase() === 'confirm') {
          let destroySub = this.store.VitalsTaskTemplate.destroy(vital.id).subscribe(
            (data) => {
              this.vitalTemplates.splice(tasksIndex, 1);
            },
            (err) => {},
            () => {
              destroySub.unsubscribe();
            }
          )
        }
      },
      (err) => {},
      () => {
        modalSub.unsubscribe();
      }
    );
  }

  public addStream() {
    this.modals.open(AddStreamComponent, {
      closeDisabled: true,
      data: {
          taskList: this.messageQueues,
          planTemplateId: this.planTemplateId,
      },
      width: '768px',
    }).subscribe((data) => {
      if (data) {
        switch (data.nextAction) {
          case 'create-stream':
            this.editStream(null);
        	case 'edit-stream':
            this.editStream(data.message);
        		break;
        	default:
        		break;
        }
      }
    });
  }

  public editStream(stream) {
    this.modals.open(CreateStreamComponent, {
      closeDisabled: true,
      data: {
        stream: stream,
        planTemplateId: this.planTemplateId,
      },
      width: '768px',
    }).subscribe((updatedStream) => {
      if (updatedStream) {
        console.log(updatedStream);
        stream = updatedStream;
      }
    });
  }

  public confirmDeleteStream() {
    this.modals.open(ConfirmModalComponent, {
     closeDisabled: true,
     data: {
       title: 'Delete Message Stream?',
       body: 'Are you sure you want to remove this message stream? This will affect X patients currently assigned to this care plan.',
       cancelText: 'Cancel',
       okText: 'confirm',
      },
      width: '384px',
    }).subscribe(() => {});
  }
}
