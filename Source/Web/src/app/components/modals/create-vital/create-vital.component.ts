import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-create-vital',
  templateUrl: './create-vital.component.html',
  styleUrls: ['./create-vital.component.scss'],
})
export class CreateVitalComponent implements OnInit {

  public data = null;

  public measures = [];

  constructor() {

  }

  public ngOnInit() {
    console.log(this.data);
  }
}
