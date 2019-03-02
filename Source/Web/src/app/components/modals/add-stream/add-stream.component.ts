import { Component, OnInit } from '@angular/core';
import { ModalService } from '../../../modules/modals';

@Component({
  selector: 'app-add-stream',
  templateUrl: './add-stream.component.html',
  styleUrls: ['./add-stream.component.scss'],
})
export class AddStreamComponent implements OnInit {

  public data = null;
  public totalPatients = 0;
  public careMessages = [];
  public searchInput = '';
  public careMessagesShown = [];
  public selectedTemplate = null;

  constructor(
    private modal: ModalService,
  ) { }

  public ngOnInit() {
    console.log(this.data);
    if (this.data) {
      this.totalPatients = this.data.totalPatients ? this.data.totalPatients : 0;
      this.careMessages = this.data.taskList ? this.data.taskList : [];
      this.careMessagesShown = this.careMessages;
    }
  }

  public filterMessages() {
    this.careMessagesShown = this.careMessages.filter((obj) => {
      return obj.name.toLowerCase().indexOf(this.searchInput) > -1;
    });
  }

  public clickEditMessage(message) {
    this.modal.close({
      nextAction: 'edit-stream',
      message: message,
    });
  }

  public clickDeleteMessage() {

  }

  public clickNewStream() {
    this.modal.close({
      nextAction: 'create-stream',
    });
  }

  public clickCancel() {
    this.modal.close(null);
  }

  public clickNext() {
    this.modal.close({
      nextAction: 'edit-stream',
      message: this.selectedTemplate,
    });
  }

  public nextDisabled() {
    return !this.selectedTemplate;
  }
}
