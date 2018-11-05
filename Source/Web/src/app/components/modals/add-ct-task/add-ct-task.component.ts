import { Component, OnInit } from '@angular/core';
import { ModalService } from '../../../modules/modals';
import { StoreService } from '../../../services';

@Component({
  selector: 'app-add-ct-task',
  templateUrl: './add-ct-task.component.html',
  styleUrls: ['./add-ct-task.component.scss'],
})
export class AddCTTaskComponent implements OnInit {

  public data = null;
  public selectedTask = null;
  public tasks = [];
  public newTaskName: string = '';

  constructor(
    private modal: ModalService,
    private store: StoreService
  ) {
  }

  public ngOnInit() {
    console.log(this.data);
    this.tasks=this.data.careTeamTasks;
  }
  public updateTaskName(task) {
    this.store.TeamTaskTemplate.update(task.id,task).subscribe((resp)=> {
       console.log(resp);
    });

  }
  public addTask(taskName) {
    if ( taskName.length <=0) {
      return;
    }
    // this.store.TeamTaskTemplate.create();
    let task = {
      start_on_day:0,
      appear_time: '00:00:00',
      due_time: '00:00:00',
      name: taskName,
      plan_template: this.data.planTemplateId,
      category: 'interaction'
    }
    this.store.TeamTaskTemplate.create(task).subscribe((resp) =>{
      this.tasks.push(resp);
      this.newTaskName = '';
    });
  }
  public next(task) {
    this.modal.close(task);
    // console.log(this.selectedTask)
  }
  public close() {
    this.modal.close(null);
  }
}
